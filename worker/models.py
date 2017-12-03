from django.db import models

class Route(models.Model):
    """Model of a transit route.

    Attributes:
        tag: Number/letter of the route, such as "N" or "38R"
        title: Title to display for the route, such as "N Judah"
    """

    tag = models.CharField(max_length=5, db_index=True, unique=True)
    title = models.TextField(max_length=40)

class Stop(models.Model):
    """Model of a single stop on a transit route.

    Attributes:
        tag: Numeric ID of the stop.
        title: Title to display for the stop, such as "Market St & Van Ness Ave"
        route_id: ID referencing a Route.
        latitude: Latitude of the stop's location.
        longitude: Longitude of the stop's location.
    """

    tag = models.IntegerField(db_index=True)
    title = models.TextField(max_length=50)
    route_id = models.ForeignKey(Route,
                                 to_field='id',
                                 on_delete=models.PROTECT)
    latitude = models.DecimalField(max_digits=8,
                                   decimal_places=5)
    longitude = models.DecimalField(max_digits=8,
                                   decimal_places=5)

    class Meta:
        unique_together = (('tag', 'route_id'),)

class ScheduleClass(models.Model):
    """Model of a schedule class, used for determining if schedules stored in the database are
    current.

    Columns:
        route_id: ID referencing a route.
        direction: The direction of travel for this schedule, either "Inbound" or "Outbound".
        service_class: The ServiceClass tag in the schedule indicating the day of the week the
            schedule applies to, either "wkd", "sat", "sun".
        name: The ScheduleClass tag for the schedule, which is a name for a schedule that is changed
            when the schedules are changed. Names are based on the date such as "2015T_FALL" or
            "2013OCTOBER"
        is_active: Boolean indicating whether this is the currently active ScheduleClass for the
            line.
    """

    route_id = models.ForeignKey(Route,
                                 to_field='id',
                                 on_delete=models.PROTECT)
    direction = models.CharField(max_length=8)
    service_class = models.CharField(max_length=3)
    name = models.TextField(max_length=20)
    is_active = models.BooleanField()

    class Meta:
        unique_together = (('route_id', 'direction', 'service_class'),)

class ScheduledArrival(models.Model):
    """Model representing a single scheduled arrival for a route at a particular stop.

    Columns:
        schedule_class: ID of the schedule class associated with this arrival.
        stop_id: ID of the stop associated with this arrival.
        block_id: Integer identifying a trip on a route.
        arrival_time: Timestamp representing milliseconds after the start of the day, indicating
            when the vehicle is scheduled to arrive at the stop.
    """

    schedule_class_id = models.ForeignKey(ScheduleClass,
                                          to_field='id',
                                          on_delete=models.PROTECT)
    stop_id = models.ForeignKey(Stop,
                                to_field='id',
                                db_index=True,
                                on_delete=models.PROTECT)
    block_id = models.IntegerField()
    arrival_time = models.IntegerField()

class Arrival(models.Model):
    """Model of a vehicle's arrival at a stop.

    Columns:
        stop_id: ID of the stop associated with this arrival.
        scheduled_arrival_id: ID of the scheduled arrival associated with this arrival.
        time: Unix timestamp indicating when the vehicle arrived at the stop.
    """

    stop_id = models.ForeignKey(Stop,
                                to_field='id',
                                db_index=True,
                                on_delete=models.PROTECT)
    scheduled_arrival_id = models.ForeignKey(ScheduledArrival,
                                             to_field='id',
                                             on_delete=models.PROTECT)
    time = models.IntegerField()
