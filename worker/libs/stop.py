"""Helper functions relating to stops"""

import configparser
import logging
import os.path as path
import py_nextbus

from worker.models import Stop
from worker.libs import utils

log = logging.getLogger(__name__)

config = configparser.ConfigParser()
#TODO: Clean this up
config.read(path.join(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))),
            'config.ini'))

def add_stops_for_route_to_database(stops, route_object):
    """Add all of the stops for a route to the database.

    Arguments:
        stops: List of dictionaries containing details of all of the stops that appear in the
                schedule, with the following keys:
                    name: String, the name of the stop, eg, "North Point St & Stockton St".
                    tag: Integer, unique ID of the stop.
        route_object: Instance of models.Route, the route to add the stops for.
    """

    log.info('Getting coordinates of stops on route')
    stop_coordinates = get_stop_coordinates_for_route(route_object.tag)

    for stop in stops:
        if stop['tag'] in stop_coordinates:
            latitude = stop_coordinates[stop['tag']]['latitude']
            longitude = stop_coordinates[stop['tag']]['longitude']
        else:
            log.warning('Could not get coordinates for stop %s in in schedule for route %s',
                        stop['tag'], route_object.tag)

        new_stop, stop_created = \
            Stop.objects.update_or_create(defaults={
                'tag': stop['tag'],
                'title': stop['name'],
                'latitude': latitude,
                'longitude': longitude,
                'route': route_object
            },
                                          route=route_object,
                                          tag=stop['tag'],
                                          latitude=latitude,
                                          longitude=longitude)
        if stop_created:
            log.info('New Stop added to database: %s', new_stop)
        else:
            log.info('Updated Stop in database with values: %s', new_stop)

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

    nextbus_client = py_nextbus.NextBusClient(output_format='json',
                                              agency=config.get('nextbus', 'agency'))
    route_config = nextbus_client.get_route_config(route_tag=route_tag)

    stops = {}

    for stop in utils.ensure_is_list(route_config['route']['stop']):
        stops[int(stop['tag'])] = {
            'latitude': float(stop['lat']),
            'longitude': float(stop['lon'])
        }

    return stops
