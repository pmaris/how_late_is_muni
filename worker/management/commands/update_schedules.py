"""Command for updating the schedules stored in the database. This is done by making a request to
the Nextbus API using the schedule command for the transit agencey specified in the config.ini file.

and then every route returned is added to the datbase if it doesn't already exist in the database,
or the title of the route is updated if it already does exist.
"""

from django.core.management.base import BaseCommand, CommandError

import configparser
import json
import logging
import os.path as path
import time

from worker.libs import route, utils
from worker.models import Route, Stop, ScheduleClass, ScheduledArrival

log = logging.getLogger(__name__)

config = configparser.ConfigParser()
#TODO: Clean this up
config.read(path.join(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))),
            'config.ini'))

class Command(BaseCommand):
    help = 'Update schedules stored in the database.'

    def handle(self, *args, **options):
        log.info('Updating schedules in database')

        for schedule_class in ScheduleClass.objects.all():
            schedule_class.is_active = False

        for schedule_route in route.get_routes():
            # Create the route in the database if it doesn't already exist
            new_route, created = \
                Route.objects.update_or_create(defaults={
                                                   'tag': schedule_route['tag'],
                                                   'title': schedule_route['title']
                                               },
                                               tag=schedule_route['tag'])
            schedule = route.get_route_schedule(route_tag=new_route.tag)
            for schedule_class in schedule:
                schedule_class_object, created = \
                    ScheduleClass.objects.get_or_create(defaults={
                                                            'route_id': new_route,
                                                            'direction': schedule_class['direction'],
                                                            'service_class': schedule_class['serviceClass'],
                                                            'name': schedule_class['scheduleClass'],
                                                            'is_active': True
                                                        },
                                                        route_id=new_route,
                                                        direction=schedule_class['direction'],
                                                        service_class=schedule_class['serviceClass'])
                if created:
                    log.info('New ScheduleClass added to database: %s', schedule_class_object)
                else:
                    log.info('Retrieved ScheduleClass from database: %s', schedule_class_object)
                for stop in schedule_class['stops']:
                    new_stop, stop_created = \
                        Stop.objects.update_or_create(defaults={
                                                          'tag': stop['tag'],
                                                          'title': stop['name'],
                                                          'route_id': new_route
                                                       },
                                                       route_id=new_route,
                                                       tag=stop['tag'])
                    if stop_created:
                        log.info('New Stop added to database: %s', new_stop)
                    else:
                        log.info('Updated Stop in database with values: %s',  new_stop)

                for trip in schedule_class['arrivals']:
                    for stop in trip['stops']:
                        # Skip stops with an arrival time of -1, which indicates that the stop
                        # is not scheduled for that trip
                        if stop['epochTime'] == -1:
                            new_scheduled_arrival = \
                                ScheduledArrival.objects.update_or_create(
                                    defaults={
                                        'schedule_class_id': schedule_class_object,
                                        'stop_id': Stop.objects.filter(route_id=new_route,
                                                                       tag=stop['tag'])[0],
                                        'block_id': trip['blockID'],
                                        'arrival_time': stop['epochTime']
                                    },
                                    schedule_class_id=schedule_class_object,
                                    stop_id=Stop.objects.filter(route_id=new_route,
                                                                tag=stop['tag'])[0],
                                    block_id=trip['blockID'])
                            if new_scheduled_arrival[1]:
                                log.info('New ScheduledArrival added to database: %s', new_scheduled_arrival)
                            else:
                                log.info('Updated ScheduledArrival in database with values: %s', new_scheduled_arrival)
