import configparser
import datetime
import logging
import os.path as path
import threading
import time

from worker.libs import route, schedule, utils
from worker.models import Route
from worker.route_worker import RouteWorker

from py_nextbus import NextBusClient

LOG = logging.getLogger()

config = configparser.ConfigParser()
#TODO: Clean this up
config.read(path.join(path.dirname(path.dirname(path.abspath(__file__))),
            'config.ini'))

class RouteManager(object):

    def __init__(self):
        self.agency = config.get('nextbus', 'agency')
        self.day_switch_time = int(config.get('worker', 'day_switch_time'))
        self.workers = []
        self.switch_day(previous_service_class=None)

    def run(self):
        current_day = datetime.date.today()

        self.start_workers()

        try:
            while True:
                new_day = datetime.date.today()
                if new_day != current_day:
                    day_time = utils.get_seconds_since_midnight()
                    if day_time > self.day_switch_time:
                        self.switch_day(previous_service_class=self.service_class)

                time.sleep(60)

        except KeyboardInterrupt:
            raise Exception('STOP NOW')
            self.stop_workers()

    def start_workers(self):
        """Start workers for all active routes."""

        LOG.info('Starting all workers')

        self.workers = []
        for route in self.active_routes:
            LOG.info('Starting worker for route %s', route.tag)
            worker = RouteWorker(route_tag=route.tag,
                                 agency=self.agency,
                                 service_class=self.service_class)
            worker.start()
            self.workers.append(worker)
    def stop_workers(self):
        """Stop all running threads."""

        LOG.info('Stopping all workers')

        for worker in self.workers:
            worker.is_running = False
            worker.join()

    def switch_day(self, previous_service_class):
        """Tasks to perform when switching to a new day.

        Arguments:
            previous_service_class: (String) The service class of the previous day, which is being
                switched away from. Either "wkd", "sat", or "sun".
        """

        LOG.info('Switching day')

        self.check_for_new_schedules()

        self.service_class = utils.get_current_service_class()
        self.active_routes = Route.objects.filter(schedule_class__is_active=True,
                                                  schedule_class__service_class=self.service_class)

        self.stop_workers()
        self.start_workers()

    def check_for_new_schedules(self):
        """Check the NextBus API for any new schedules that have been published, and add any new
        schedules or new routes to the database."""

        # Check if there are any new routes
        routes = route.get_routes(self.agency)
        route.add_routes_to_database(routes)

        threads = []
        for r in routes:
            thread = threading.Thread(target=schedule.update_schedule_for_route,
                                      args=(Route.objects.get(tag=r['tag'])),)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
