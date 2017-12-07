"""Helper functions relating to schedules."""

import configparser
import logging
import os.path as path

from worker.models import ScheduledArrival, ScheduleClass, Stop
from worker.libs import route, stop

log = logging.getLogger(__name__)

config = configparser.ConfigParser()
#TODO: Clean this up
config.read(path.join(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))),
            'config.ini'))

def update_schedule_for_route(route_object):
    """Update the schedule stored in the database for a single route.

    Arguments:
        route_object: Instance of models.Route, the route to update the schedule for.
    """

    schedules = route.get_route_schedule(route_tag=route_object.tag)

    for schedule_class in schedules:
        schedule_class_object, created = \
            ScheduleClass.objects.get_or_create(defaults={
                'route_id': route_object,
                'direction': schedule_class['direction'],
                'service_class': schedule_class['serviceClass'],
                'name': schedule_class['scheduleClass'],
                'is_active': True
            },
                                                route_id=route_object,
                                                direction=schedule_class['direction'],
                                                service_class=schedule_class['serviceClass'])
        if created:
            log.info('New ScheduleClass added to database: %s', schedule_class_object)
        else:
            log.info('Retrieved ScheduleClass from database: %s', schedule_class_object)

        stop.add_stops_for_route_to_database(stops=schedule_class['stops'],
                                             route_object=route_object)

        for trip in schedule_class['arrivals']:
            for trip_stop in trip['stops']:
                # Skip stops with an arrival time of -1, which indicates that the stop
                # is not scheduled for that trip
                if trip_stop['epochTime'] == -1:
                    new_scheduled_arrival = \
                        ScheduledArrival.objects.update_or_create(
                            defaults={
                                'schedule_class_id': schedule_class_object,
                                'stop_id': Stop.objects.filter(route_id=route_object,
                                                               tag=trip_stop['tag'])[0],
                                'block_id': trip['blockID'],
                                'arrival_time': trip_stop['epochTime']
                            },
                            schedule_class_id=schedule_class_object,
                            stop_id=Stop.objects.filter(route_id=route_object,
                                                        tag=trip_stop['tag'])[0],
                            block_id=trip['blockID'])
                    if new_scheduled_arrival[1]:
                        log.info('New ScheduledArrival added to database: %s', new_scheduled_arrival)
                    else:
                        log.info('Updated ScheduledArrival in database with values: %s',
                                 new_scheduled_arrival)
