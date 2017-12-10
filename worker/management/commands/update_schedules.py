"""Command for updating the schedules stored in the database. This is done by making a request to
the Nextbus API using the schedule command for the transit agencey specified in the config.ini file.

and then every route returned is added to the datbase if it doesn't already exist in the database,
or the title of the route is updated if it already does exist.
"""

import configparser
import logging
import os.path as path

from django.core.management.base import BaseCommand, CommandError

from worker.libs import route, schedule
from worker.models import Route, ScheduleClass

log = logging.getLogger(__name__)

config = configparser.ConfigParser()
#TODO: Clean this up
config.read(path.join(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))),
            'config.ini'))

class Command(BaseCommand):
    help = 'Update schedules stored in the database. If the --route argument is not provided, all '\
           'routes will be updated.'

    def add_arguments(self, parser):
        parser.add_argument('--route',
                            dest='route_tag',
                            help='Update the schedule for the provided route instead of all of ' \
                                  'the routes for the transit agency. The value must be a route ' \
                                  'tag matching the tag of an existing route for the transit ' \
                                  'agency.')

    def handle(self, *args, **options):
        log.info('Updating schedules in database')

        # Update all routes if one wasn't specified
        if options['route_tag'] is None:
            # Deactivate all existing ScheduleClasses in the database
            for schedule_class in ScheduleClass.objects.all():
                schedule_class.is_active = False
                schedule_class.save()

            routes = route.get_routes()
            route.add_routes_to_database(routes)
            for r in routes:
                schedule.update_schedule_for_route(Route.objects.get(tag=r['tag']))

        # Update provided route
        else:
            routes = route.get_routes()

            # Check if provided route is an existing route for the agency
            matching_route = list(filter(lambda r: r['tag'] == options['route_tag'], routes))
            if matching_route:
                route.add_routes_to_database(matching_route)
                route_object = Route.objects.get(tag=options['route_tag'])

                # Deactivate all existing ScheduleClasses for the route in the database
                for schedule_class in ScheduleClass.objects.filter(route_id=route_object):
                    schedule_class.is_active = False
                    schedule_class.save()

                schedule.update_schedule_for_route(route_object)
            else:
                raise CommandError('Route %s is not a valid route' % options['route_tag'])