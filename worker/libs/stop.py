"""Helper functions relating to stops"""

import configparser
import logging
import os.path as path
import py_nextbus

import how_late_is_muni.settings as settings
from worker.models import Stop
from worker.libs import utils

log = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read(path.join(settings.BASE_DIR, 'config.ini'))

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

    stop_list = []
    for stop in stops:
        if stop['tag'] in stop_coordinates:
            stop_list.append([
                route_object.id,
                stop['tag'],
                stop['name'],
                stop_coordinates[stop['tag']]['latitude'],
                stop_coordinates[stop['tag']]['longitude']
            ])

        else:
            log.warning('Could not get coordinates for stop %s in in schedule for route %s',
                        stop['tag'], route_object.tag)
            latitude = None
            longitude = None


    utils.bulk_insert(table_name=Stop._meta.db_table,
                      column_names=['route_id', 'tag', 'title', 'latitude', 'longitude'],
                      update_columns=['route_id', 'title', 'latitude', 'longitude'],
                      data=stop_list)

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
