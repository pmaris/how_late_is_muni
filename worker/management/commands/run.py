import configparser
import logging
import os.path as path

from django.core.management.base import BaseCommand, CommandError

import worker.libs.utils as utils
from worker.models import Route
from worker.route_manager import RouteManager
from worker.route_worker import RouteWorker

log = logging.getLogger(__name__)

config = configparser.ConfigParser()
#TODO: Clean this up
config.read(path.join(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))),
            'config.ini'))

class Command(BaseCommand):
    help = 'Run the worker to get arrivals'

    def add_arguments(self, parser):
        parser.add_argument('--route',
                            dest='route_tag',
                            help='Run the worker only for the provided route instead of all of ' \
                                  'the routes for the transit agency. The value must be a route ' \
                                  'tag matching the tag of an existing route for the transit ' \
                                  'agency.')

    def handle(self, *args, **options):

        # Get currently active routes. The routes will have to be updated when the schedules change.
        active_routes = Route.objects.filter(schedule_class__is_active=True)
        active_route_tags = [route.tag for route in active_routes]

        service_class = utils.get_current_service_class()

        if options['route_tag'] is None:

            manager = RouteManager()
        else:
            if options['route_tag'] not in active_route_tags:
                raise CommandError('Route %s is not a valid route' % options['route_tag'])

            else:
                route_worker = RouteWorker(route_tag=options['route_tag'],
                                           agency=config.get('nextbus', 'agency'),
                                           service_class=service_class)
                route_worker.run()
