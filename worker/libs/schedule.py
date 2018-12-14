"""Helper functions relating to schedules."""

import configparser
import logging
import os.path as path

import how_late_is_muni.settings as settings
from worker.models import ScheduledArrival, ScheduleClass, Stop, StopScheduleClass
from worker.libs import route, stop, utils

LOG = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read(path.join(settings.BASE_DIR, 'config.ini'))

def update_schedule_for_route(route_object):
    """Update the schedule stored in the database for a single route.

    Arguments:
        route_object: Instance of models.Route, the route to update the schedule for.
    """

    schedules = route.get_route_schedule(route_tag=route_object.tag)
    if schedules is None:
        return

    schedules_to_add = []
    # Check if each combination of schedule class, service class, and direction already exists in
    # the database for the route
    for schedule in schedules:
        try:
            existing_schedule_class = \
                ScheduleClass.objects.get(route=route_object,
                                          direction=schedule.get('direction'),
                                          service_class=schedule.get('serviceClass'))
        except ScheduleClass.DoesNotExist:
            schedules_to_add.append(schedule)

        else:
            # If there is already a schedule class in the database for the route for the same
            # direction but with a different name, deactivate thie existing schedule class and add
            # a one with the new name
            if existing_schedule_class.name != schedule.get('scheduleClass'):
                schedules_to_add.append(schedule)

                existing_schedule_class.is_active = False
                existing_schedule_class.save()

    if not schedules_to_add:
        LOG.info('No new schedules were found')
        return

    # Deactivate all existing ScheduleClasses for the route in the database
    ScheduleClass.objects.filter(route_id=route_object).update(is_active=False)

    # Get unique stops for the route
    stops = []
    stop_tags = []
    for schedule_class in schedules_to_add:
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
    stop_schedule_classes = set()
    stop_schedule_class_dicts = []
    scheduled_arrivals = []

    for schedule_class in schedules_to_add:
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
            LOG.info('New ScheduleClass added to database: %s', schedule_class_object)
        else:
            LOG.info('Retrieved ScheduleClass from database: %s', schedule_class_object)

        schedule_classes.append(schedule_class_object)

        for trip in schedule_class['arrivals']:
            for order, trip_stop in enumerate(trip['stops'], 1):
                # Skip stops with an arrival time of -1, which indicates that the stop
                # is not scheduled for that trip
                if trip_stop['epochTime'] != -1:
                    # Get the stop for the arrival, without querying the database. If the stop for
                    # the arrival isn't one of the stops retrieved from the database, don't add the
                    # arrival to the database.
                    db_stop = [stop for stop in route_stops if stop.tag == trip_stop['tag']]
                    if not db_stop:
                        continue

                    stop_schedule_class = {
                        'stop_id': db_stop[0].id,
                        'schedule_class_id': schedule_class_object.id,
                        'stop_order': order
                    }

                    if (db_stop[0].id, schedule_class_object.id) not in stop_schedule_classes:
                        stop_schedule_classes.add((db_stop[0].id, schedule_class_object.id))
                        stop_schedule_class_dicts.append(stop_schedule_class)

                    # Time is returned in milliseconds, convert to seconds to make easier to
                    # work with
                    arrival_time = trip_stop['epochTime'] / 1000

                    # Arrivals after midnight that are part of the same service day have timestamps
                    # that are greater than 24 hours from the midnight epoch. In this case, remove
                    # 24 hours from the timestamp to simplify comparisons.
                    if arrival_time >= 60 * 60 * 24:
                        arrival_time -= 60 * 60 * 24

                    # Add details for the scheduled arrivals that can be added now. The details of
                    # the stop schedule class will be used to lookup the stop schedule class in
                    # the database before adding the scheduled arrival to the database.
                    scheduled_arrivals.append({
                        'block_id': trip['blockID'],
                        'time': arrival_time,
                        'stop_schedule_class_dict': stop_schedule_class
                    })

    utils.bulk_upsert(model=StopScheduleClass,
                      data=stop_schedule_class_dicts,
                      update_on_conflict=False,
                      conflict_columns=['stop_id', 'schedule_class_id', 'stop_order'])

    stop_schedule_class_objects = \
        StopScheduleClass.objects.filter(schedule_class__in=schedule_classes,
                                         stop__in=route_stops)

    for scheduled_arrival in scheduled_arrivals:
        stop_schedule_class = scheduled_arrival.pop('stop_schedule_class_dict')

        scheduled_arrival['stop_schedule_class'] = \
            [ssc for ssc in stop_schedule_class_objects if \
                ssc.stop_id == stop_schedule_class['stop_id'] and \
                ssc.schedule_class_id == stop_schedule_class['schedule_class_id'] and \
                ssc.stop_order == stop_schedule_class['stop_order']][0]

    # Remove possible duplicate arrivals
    unique_scheduled_arrivals = []
    for scheduled_arrival in scheduled_arrivals:
        if scheduled_arrival not in unique_scheduled_arrivals:
            unique_scheduled_arrivals.append(scheduled_arrival)
    utils.bulk_upsert(model=ScheduledArrival,
                      data=unique_scheduled_arrivals,
                      update_on_conflict=False,
                      conflict_columns=['stop_schedule_class_id', 'block_id', 'time'])
