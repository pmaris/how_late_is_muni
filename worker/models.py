from django.db import models

class Route(models.Model):
    """Model of a transit route.

    Attributes:
        tag: Number/letter of the route, such as "N" or "38R"
        title: Title to display for the route, such as "N Judah"
    """

    tag = models.CharField(max_length=5, db_index=True, unique=True)
    title = models.TextField(max_length=40)

    class Meta:
        db_table = 'route'

class Stop(models.Model):
    """Model of a single stop on a transit route.

    Attributes:
        tag: Numeric ID of the stop.
        title: Title to display for the stop, such as "Market St & Van Ness Ave"
        route: The Route the stop is on.
        latitude: Latitude of the stop's location.
        longitude: Longitude of the stop's location.
    """

    tag = models.IntegerField(db_index=True)
    title = models.TextField(max_length=50)
    route = models.ForeignKey(Route,
                              on_delete=models.PROTECT,
                              related_name='stop')
    latitude = models.DecimalField(max_digits=8,
                                   decimal_places=5,
                                   null=True)
    longitude = models.DecimalField(max_digits=8,
                                    decimal_places=5,
                                    null=True)

    class Meta:
        unique_together = (('tag', 'route'),)
        db_table = 'stop'

class ScheduleClass(models.Model):
    """Model of a schedule class, used for determining if schedules stored in the database are
    current.

    Columns:
        route: The Route the ScheduleClass is for.
        direction: The direction of travel for this schedule, either "Inbound" or "Outbound".
        service_class: The ServiceClass tag in the schedule indicating the day of the week the
            schedule applies to, either "wkd", "sat", "sun".
        name: The ScheduleClass tag for the schedule, which is a name for a schedule that is changed
            when the schedules are changed. Names are based on the date such as "2015T_FALL" or
            "2013OCTOBER"
        is_active: Boolean indicating whether this is the currently active ScheduleClass for the
            line.
    """

    route = models.ForeignKey(Route,
                              on_delete=models.PROTECT,
                              related_name='schedule_class')
    direction = models.CharField(max_length=8)
    service_class = models.CharField(max_length=3)
    name = models.TextField(max_length=20)
    is_active = models.BooleanField()

    class Meta:
        unique_together = (('route', 'direction', 'service_class'),)
        db_table = 'schedule_class'

class StopScheduleClass(models.Model):
    """Model of an association between stops and schedule classes.

    Columns:
        stop: The Stop this schedule class is associated with.
        schedule_class: The schedule class the stop is associated with.
        stop_order: Position of the stop along the route relative to the other stops for the route
            in the schedule class. Ordering starts at 1 for the first stop on the route, and
            increments by 1 for each successive stop.
    """

    stop = models.ForeignKey(Stop,
                             on_delete=models.PROTECT,
                             related_name='stop_schedule_class')
    schedule_class = models.ForeignKey(ScheduleClass,
                                       on_delete=models.PROTECT,
                                       related_name='stop_schedule_class')
    stop_order = models.IntegerField()

    class Meta:
        unique_together = (('stop', 'schedule_class', 'stop_order'),)
        db_table = 'stop_schedule_class'

class ScheduledArrival(models.Model):
    """Model representing a single scheduled arrival for a route at a particular stop.

    Columns:
        stop_schedule_class: The stop schedule class associated with this arrival.
        block_id: Integer identifying a trip on a route.
        time: Timestamp representing seconds after the start of the day, indicating when the vehicle
            is scheduled to arrive at the stop.
    """

    stop_schedule_class = models.ForeignKey(StopScheduleClass,
                                            on_delete=models.PROTECT,
                                            related_name='scheduled_arrival')
    block_id = models.IntegerField()
    time = models.IntegerField()

    class Meta:
        unique_together = (('stop_schedule_class', 'block_id', 'time'),)
        db_table = 'scheduled_arrival'

class Arrival(models.Model):
    """Model of a vehicle's arrival at a stop.

    Columns:
        stop: The Stop associated with this arrival.
        scheduled_arrival: The Scheduled Arrival associated with this arrival.
        time: Unix timestamp indicating when the vehicle arrived at the stop.
    """

    stop = models.ForeignKey(Stop,
                             on_delete=models.PROTECT)
    scheduled_arrival = models.ForeignKey(ScheduledArrival,
                                          on_delete=models.PROTECT,
                                          related_name='arrival')
    time = models.IntegerField()

    class Meta:
        unique_together = (('stop', 'scheduled_arrival', 'time'),)
        db_table = 'arrival'
