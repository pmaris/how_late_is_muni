"""Helper functions relating to routes."""

import configparser
from datetime import time
import os.path as path

from . import utils

config = configparser.ConfigParser()
#TODO: Clean this up
config.read(path.join(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))),
            'config.ini'))

def get_routes():
    """Get all existing routes on NextBus for a transit agency.

    Returns:
        List of dictionaries for each route containing the following keys:
            tag: String, short name of the route, eg, "38R".
            title: String, title of the route, eg, "38R-Geary Rapid".
        route.
    """
    params = {
        'command': 'routeList',
        'a': config.get('nextbus', 'agency')
    }
    nextbus_response = utils.nextbus_request(url=config.get('nextbus', 'api_url'),
                                          params=params)

    return utils.ensure_is_list(nextbus_response['route'])

def get_route_schedule(route_tag):
    """Gets the schedule for a single route.

    Arguments:
        route_tag: String, the route tag of the route to retrieve the schedule for.

    Returns:
        List of dictionaries for each service class (Schedule for one direction for a day of the
        week) for the route, containing the following keys:
            arrivals: List of dictionaries containing the details of the scheduled arrivals. Each
                dictionary has the following keys:
                    blockID: Integer. The block ID identifies a single vehicle across multiple
                        trips throughout the day.
                    stops: List of dictionaries containing the details of the scheduled arrival
                        for each stop, with the following keys:
                            epochTime: Integer, timestamp of of the scheduled arrival time, with the
                                epoch being the start of the day. The value will be -1 if the stop
                                is skipped on a particular trip.
                            tag: Integer, stop tag uniquely identifying the stop.
                            time: Time object of the scheduled arrival time, or None if the stop is
                                skipped on the particular trip.
            direction: String indicating which direction on the route the schedule is for, either
                "Inbound" or "Outbound".
            scheduleClass: String with a name of the current schedule. When a new schedule is
                published, this will change.
            serviceClass: String indicating the day of the week the schedule is for, either "wkd"
                (For weekdays), "sat", or "sun".
            stops: List of dictionaries containing details of all of the stops that appear in the
                schedule, with the following keys:
                    name: String, the name of the stop, eg, "North Point St & Stockton St".
                    tag: Integer, unique ID of the stop.
            tag: String, short name of the route, eg, "38R".
            title: String, title of the route, eg, "38R-Geary Rapid".
    """

    params = {
        'command': 'schedule',
        'a': config.get('nextbus', 'agency'),
        'r': route_tag
    }
    nextbus_response = utils.nextbus_request(url=config.get('nextbus', 'api_url'),
                                             params=params)

    response = []
    for schedule in utils.ensure_is_list(nextbus_response['route']):
        arrivals = []
        for trip in utils.ensure_is_list(schedule['tr']):
            stops = []
            for stop in utils.ensure_is_list(trip['stop']):
                epoch_time = int(stop['epochTime'])
                if epoch_time != -1:
                    hours, minutes, seconds = stop['content'].split(':')
                    stops.append({
                        'epochTime': epoch_time,
                        'tag': int(stop['tag']),
                        'time': time(hour=int(hours),
                                     minute=int(minutes),
                                     second=int(seconds))
                    })
                else:
                    stops.append({
                        'epochTime': epoch_time,
                        'tag': int(stop['tag']),
                        'time': None
                    })
                arrivals.append({
                    'stops': stops,
                    'blockID': int(trip['blockID'])
                })

        stops = []
        for stop in utils.ensure_is_list(schedule['header']['stop']):
            stops.append({
                'name': stop['content'],
                'tag': int(stop['tag'])
            })

        response.append({
            'arrivals': arrivals,
            'direction': schedule['direction'],
            'scheduleClass': schedule['scheduleClass'],
            'serviceClass': schedule['serviceClass'],
            'stops': stops,
            'tag': schedule['tag'],
            'title': schedule['title']
        })

    return response
