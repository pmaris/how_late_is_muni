"""Helper functions relating to stops"""

import configparser
from datetime import time
import os.path as path

from . import utils

config = configparser.ConfigParser()
#TODO: Clean this up
config.read(path.join(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))),
            'config.ini'))

def get_stop_coordinates_for_route(route_tag):
    """Get the latitude and longitude of all of the stops on a route.

    Arguments:
        route_tag: String, the route tag of the route to get the stop coordinates for.

    Returns:
        A dictionary with stop tags as keys (As integers) and dictionaries containing the following
        keys as values:
            latitude: Float, the latitude of the stop's location.
            longitude: Float, the longitude of the stop's location.
    """

    params = {
        'command': 'routeConfig',
        'a': config.get('nextbus', 'agency'),
        'r': route_tag
    }
    nextbus_response = utils.nextbus_request(url=config.get('nextbus', 'api_url'),
                                             params=params)

    stops = {}

    for stop in utils.ensure_is_list(nextbus_response['route']['stop']):
        stops[int(stop['tag'])] = {
            'latitude': float(stop['lat']),
            'longitude': float(stop['lon'])
        }

    return stops
