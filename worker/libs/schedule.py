"""Helper functions relating to schedules."""

import configparser
import logging
import os.path as path

from worker.models import ScheduledArrival, ScheduleClass, Stop, StopScheduleClass
from worker.libs import route, stop, utils

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
    if schedules is None:
        return

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

    # Get all stops for the route from the database, including the routes that were just added, so
    # that each stop doesn't need to be repeatedly retrieved from the database when adding stop
    # schedule classes
    route_stops = Stop.objects.filter(route=route_object)

    schedule_classes = []
    stop_schedule_classes = []
    scheduled_arrivals = []

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

        schedule_classes.append(schedule_class_object)

        for trip in schedule_class['arrivals']:
            for order, trip_stop in enumerate(trip['stops'], 1):
                # Skip stops with an arrival time of -1, which indicates that the stop
                # is not scheduled for that trip
                if trip_stop['epochTime'] != -1:
                    # Get the stop for the arrival, without querying the database
                    db_stop = [stop for stop in route_stops if stop.tag == trip_stop['tag']][0]

                    stop_schedule_classes.append([
                        db_stop.id,
                        schedule_class_object.id,
                        order
                    ])

                    # Add details for the scheduled arrivals that can be added now. The ID of the
                    # stop schedule class will be appended to the data once the stop schedule
                    # classes are inserted into the database
                    scheduled_arrivals.append([
                        trip['blockID'],
                        trip_stop['epochTime']
                    ])

    utils.bulk_insert(table_name=StopScheduleClass._meta.db_table,
                      column_names=['stop_id', 'schedule_class_id', 'stop_order'],
                      data=stop_schedule_classes,
                      ignore_duplicates=True)

    stop_schedule_class_objects = \
        StopScheduleClass.objects.filter(schedule_class__in=schedule_classes,
                                         stop__in=route_stops)

    # Go back through all of the stop schedule classes that were added to bulk insert all of the
    # scheduled arrivals for them
    for i, stop_schedule_class_data in enumerate(stop_schedule_classes):
        stop_id, schedule_class_id, order = stop_schedule_class_data
        stop_schedule_class = \
            [ssc for ssc in stop_schedule_class_objects if ssc.stop_id == stop_id and \
                                                           ssc.schedule_class_id == schedule_class_id and \
                                                           ssc.stop_order == order][0]
        scheduled_arrivals[i].append(stop_schedule_class.id)

    utils.bulk_insert(table_name=ScheduledArrival._meta.db_table,
                      column_names=['block_id', 'arrival_time', 'stop_schedule_class_id'],
                      data=scheduled_arrivals,
                      ignore_duplicates=True)
