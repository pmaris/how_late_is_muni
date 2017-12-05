import logging

from django.core.management.base import BaseCommand, CommandError

from worker.models import Route, ScheduleClass

log = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Run main loop'

    def handle(self, *args, **options):

        # First get all active routes. THIS WILL HAVE TO BE DYNAMICALLY UPDATED WHEN THE SCHEDULES CHANGE
        schedule_classes = ScheduleClass.objects.filter(is_active=True).values('route_id')
        active_routes = Route.objects.filter(id__in(schedule_classes))
        print(routes.objects.all())

        # First, create instances of class for each route

        # Start running each class in a thread

        # Should each route independently handle iteration and things like starting and stopping when
        # the route is running, or handle here?
        pass