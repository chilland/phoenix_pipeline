from __future__ import unicode_literals
from __future__ import print_function
import json
import requests
import utilities
from bson.objectid import ObjectId


def query_cliff(sentence):
    """
    Filters out duplicate events, leaving only one unique
    (DATE, SOURCE, TARGET, EVENT) tuple per day.


    Parameters
    ----------

    sentence: String.
                Text from which an event was coded.

    Returns
    -------

    lat: String.
            Latitude of a location.

    lon: String.
            Longitude of a location.
    """
    
    payload = {"q":sentence}
    
    place_info = {'lat':'', 'lon':'', 'placename':'', 'country':'', 'restype':''}

    try:
        located = requests.get("http://localhost:8999/CLIFF-2.0.0/parse/text",
                params=payload).json     # convert all at once. Good practice?
    
    except Exception as e:
        print('There was an error requesting geolocation. {}'.format(e))
        located = place_info
    
    if located:
        try:
            focus = located['results']['places']['focus']
        except Exception as e:
            print('There was an error: {}. Status code: {}'.format(e,
                                                                   focus.status_code))
    
            place_info = {'lat':'', 'lon':'', 'placename':'', 'country':'', 'restype':''}
    
    else:
        place_info = {'lat':'', 'lon':'', 'placename':'', 'country':'', 'restype':''}
    
 # If there's a city, we want that.
    if focus['cities']:
        # If there's more than onne city, we just want the first.
        # (That's questionable, but eh)
        if len(focus['cities']) > 1:
            citylist = focus['cities'][0]
            lat = citylist['lat']
            lon = citylist['lon']
            placename = citylist['name']
            country = citylist['countryCode']
            place_info = {'lat':lat, 'lon':lon, 'placename':placename, 'restype':'city'}
        # If there's only one city, we're good to go.
        if len(focus['cities']) == 1:
            #print("This thing thinks there's only one city")
            lat = focus['cities'][0]['lat']
            lon = focus['cities'][0]['lon']
            placename = focus['cities'][0]['name']
            country = focus['cities'][0]['countryCode']
            place_info = {'lat':lat, 'lon':lon, 'placename':placename, 'restype':'city', 'country':country}
    # If there's no city, we'll take a state.
    if (len(focus['states']) > 0) & (len(focus['cities']) == 0):        
        #if len(focus['states']) > 1:
        #    stateslist = focus['states'][0]
        #    lat = stateslist['states']['lat']
        #    lon = stateslist['states']['lon']
        #    placename = statelist['states']['name']
        if len(focus['states']) == 1:
            lat = focus['states'][0]['lat']
            lon = focus['states'][0]['lon']
            placename = focus['states'][0]['name']
            place_info = {'lat':lat, 'lon':lon, 'placename':placename, 'restype':'state'}
        else:
            print("WTF, states are too long")
    #if ((focus['cities'] == []) & len(focus['states']) > 0):
       # lat = focus['cities']['lat']
       # lon = focus['cities']['lon']
       # placename = focus['cities']['name']
    if (len(focus['cities']) == 0) & (len(focus['states'])==0):
        print("daaaang, it's countries")
        lat = focus['countries'][0]['lat']
        lon = focus['countries'][0]['lon']
        placename = focus['countries'][0]['name']
        place_info = {'lat':lat, 'lon':lon, 'placename':placename, 'restype':'country'}

    return place_info 


def main(events, file_details):
    """
    Pulls out a database ID and runs the ``query_geotext`` function to hit the
    GeoVista Center's GeoText API and find location information within the
    sentence.

    Parameters
    ----------

    events: Dictionary.
            Contains filtered events from the one-a-day filter. Keys are
            (DATE, SOURCE, TARGET, EVENT) tuples, values are lists of
            IDs, sources, and issues.

    Returns
    -------

    events: Dictionary.
            Same as in the parameter but with the addition of a value that is
            a tuple of the form (LAT, LON).
    """
    coll = utilities.make_conn(file_details.auth_db, file_details.auth_user,
                               file_details.auth_pass)

    for event in events:
        event_id, sentence_id = events[event]['ids'][0].split('_')
        result = coll.find_one({'_id': ObjectId(event_id.split('_')[0])})
        sents = utilities.sentence_segmenter(result['content'])

        query_text = sents[int(sentence_id)]
        geo_info = query_cliff(query_text)
        if geo_info:
            events[event]['geo'] = (geo_info['lon'], geo_info['lat'], geo_info['placename'])
            # Add in country and restype here
    return events
