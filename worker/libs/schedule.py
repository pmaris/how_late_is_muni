"""Helper functions relating to schedules."""

import configparser
import logging
import os.path as path

from worker.models import ScheduledArrival, ScheduleClass, Stop, StopScheduleClass
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

    # Get unique stops for the route
    stops = []
    stop_tags = []
    for schedule_class in schedules:
        for schedule_class_stop in schedule_class['stops']:
            if schedule_class_stop['tag'] not in stop_tags:
                stops.append(schedule_class_stop)
                stop_tags.append(schedule_class_stop['tag'])

    stop.add_stops_for_route_to_database(stops=stops,
                                         route_object=route_object)
    for schedule_class in schedules:
        schedule_class_object, created = \
            ScheduleClass.objects.get_or_create(defaults={
                'route': route_object,
                'direction': schedule_class['direction'],
                'service_class': schedule_class['serviceClass'],
                'name': schedule_class['scheduleClass'],
                'is_active': True
            },
                                                route=route_object,
                                                direction=schedule_class['direction'],
                                                service_class=schedule_class['serviceClass'])
        if created:
            log.info('New ScheduleClass added to database: %s', schedule_class_object)
        else:
            log.info('Retrieved ScheduleClass from database: %s', schedule_class_object)

        for trip in schedule_class['arrivals']:
            for order, trip_stop in enumerate(trip['stops'], 1):
                # Skip stops with an arrival time of -1, which indicates that the stop
                # is not scheduled for that trip
                if trip_stop['epochTime'] != -1:
                    print(trip_stop['tag'])
                    db_stop = Stop.objects.get(route=route_object,
                                               tag=trip_stop['tag'])
                    stop_schedule_class, _ = \
                        StopScheduleClass.objects.update_or_create(defaults={
                                'stop': db_stop,
                                'schedule_class': schedule_class_object,
                                'stop_order': order
                            },
                            stop=db_stop,
                            schedule_class=schedule_class_object,
                            stop_order=order)

                    new_scheduled_arrival, arrival_created = \
                        ScheduledArrival.objects.update_or_create(
                            defaults={
                                'stop_schedule_class': stop_schedule_class,
                                'block_id': trip['blockID'],
                                'arrival_time': trip_stop['epochTime']
                            },
                            stop_schedule_class=stop_schedule_class,
                            block_id=trip['blockID'],
                            arrival_time=trip_stop['epochTime'])
                    if arrival_created:
                        log.info('New ScheduledArrival added to database: %s', new_scheduled_arrival)
                    else:
                        log.info('Updated ScheduledArrival in database with values: %s',
                                 new_scheduled_arrival)
