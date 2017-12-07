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
    help = 'Update schedules stored in the database.'

    def handle(self, *args, **options):
        log.info('Updating schedules in database')

        for schedule_class in ScheduleClass.objects.all():
            schedule_class.is_active = False

        routes = route.get_routes()
        route.add_routes_to_database(routes)
        for r in routes:
            schedule.update_schedule_for_route(Route.objects.get(tag=r['tag']))
