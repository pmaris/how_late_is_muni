import configparser
import logging
import os.path as path

from django.core.management.base import BaseCommand, CommandError

import how_late_is_muni.settings as settings
import worker.libs.utils as utils
from worker.models import Route, ScheduleClass
from worker.route_manager import RouteManager
from worker.route_worker import RouteWorker

LOG = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read(path.join(settings.BASE_DIR, 'config.ini'))

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
        if options['route_tag'] is None:
            manager = RouteManager()
        else:
            service_class = utils.get_current_service_class()
            active_schedule_classes = ScheduleClass.objects.filter(is_active=True,
                                                                   service_class=service_class)\
                                                           .values_list('route_id', flat=True)
            active_route_tags = Route.objects.filter(id__in=active_schedule_classes).values_list('tag', flat=True)

            if options['route_tag'] not in active_route_tags:
                raise CommandError('Route %s is not a valid route' % options['route_tag'])

            else:
                route_worker = RouteWorker(route_tag=options['route_tag'],
                                           agency=config.get('nextbus', 'agency'),
                                           service_class=service_class)
                route_worker.run()

                LOG.warning('Worker stopped running')
