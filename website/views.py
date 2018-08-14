import datetime
from django.core.exceptions import ValidationError
from django.db.models import Count, F, Func, Subquery
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

import worker.libs.utils as utils
import website.libs.validators as validators
from worker.models import Arrival, Route, ScheduleClass, Stop

def index(request):
    """Render the website's index page."""

    return render(request, 'index.html')

def routes(request):
    """Controller for handling requests for routes."""

    if request.method == 'GET':
        return get_routes(request)
    else:
        return HttpResponse(status=404,
                            reason='Not found')

def get_routes(request):
    """Retrieve details of all of the routes in the database.

    Request path:
        GET /routes

    Query parameters:
        is_active (Optional): Boolean, filter the returned routes by whether the route is currently
            an active route that still runs. If not specified, all routes, including inactive former
            routes, are returned.

    Returns:
         A JSON response containing an array of objects for each route, with the following keys:
             tag: String, the tag for the route.
             title: String, the title of the route.
             is_active: Boolean, indicates whether the route is a route this is still actively
                 running.
    """

    is_active = request.GET.get('is_active')

    validation_errors = {}
    if is_active is not None:
        try:
            is_active = validators.validate_boolean(value=is_active)
        except ValidationError as e:
            validation_errors['is_active'] = e.messages[0]

    if validation_errors:
        return JsonResponse(data=validation_errors,
                            status=400)

    routes = Route.objects.all().annotate(active_schedule_classes=Count('schedule_class__is_active'))

    if is_active is not None:
        if is_active:
            routes = routes.filter(active_schedule_classes__gt=0)
        else:
            routes = routes.filter(active_schedule_classes=0)

    response_body = []
    for route in routes:
        response_body.append({
            'tag': route.tag,
            'title': route.title,
            'is_active': route.active_schedule_classes > 0
        })

    return JsonResponse(data=response_body,
                        status=200,
                        safe=False)

def stops(request):
    """Controller for handling requests for routes."""

    if request.method == 'GET':
        return get_stops(request)
    else:
        return HttpResponse(status=404,
                            reason='Not found')

def get_stops(request):
    """Retrieve details of the stops in the database for a route.

    Request path:
        GET /stops?stop_tag=(stop_tag)

    Query parameters:
        route_tag: (Required) String, the route tag of the route to get the stops for.
        direction: (Optional) String, either "inbound" or "outbound" (Case insensitive). If
            specified, stops will be filtered based on their direction.

    Returns:
        A JSON response containing an array of objects for each stop, with the following keys:
            tag: String, the tag for the stop.
            title: String, the title of the stop.
            latitude: Float, the latitude of the stop's location.
            longitude: Float, the longitude of the stop's location.
            direction: String, the direction on the route that the stop is on. Either "Inbound" or
                "Outbound".
            order: Integer, ordinal indicating the stop's order relative to the other stops along
                the route in the same direction.

        Stops are ordered first by direction, and then by order.
    """

    route_tag = request.GET.get('route_tag')
    direction = request.GET.get('direction')

    validation_errors = {}
    if route_tag is None:
        validation_errors['route_tag'] = 'route_tag is required'
    else:
        try:
            route_tag = validators.validate_route_tag(route_tag)
        except ValidationError as e:
            validation_errors['route_tag'] = e.messages[0]

    if direction is not None:
        try:
            direction = validate.validate_choice(value=str(direction).lower(),
                                                 valid_choices=['inbound', 'outbound'])
        except ValidationError as e:
            validation_errors['direction'] = e.messages[0]

    if validation_errors:
        return JsonResponse(data=validation_errors,
                            status=400)

    stops = Stop.objects.filter(route__tag=route_tag)

    if direction is not None:
        stops = stops.filter(stop_schedule_class__schedule_class__direction=direction.capitalize())

    stops.order_by('stop_schedule_class__schedule_class__direction',
                   'stop_schedule_class__schedule_class__stop_order')

    response_body = []
    for stop in stops:
        response_body.append({
            'tag': stop.tag,
            'title': stop.title,
            'latitude': float(stop.latitude),
            'longitude': float(stop.longitude),
            'direction': stop.stop_schedule_class.filter(schedule_class__is_active=True).first().schedule_class.direction,
            'order': stop.stop_schedule_class.filter(schedule_class__is_active=True).first().stop_order
        })

    return JsonResponse(data=response_body,
                        status=200,
                        safe=False)

def get_arrival_buckets(request):
    """Get counts of arrivals bucketed by the number of minutes away from their scheduled arrival
    time they are.

    Request path:
        GET /arrivals/buckets

    Query parameters:
        start_time: (Required) Integer, Unix timestamp indicating the earliest bound of the time of
            arrivals to count.
        end_time: (Optional) Integer, Unix timestamp indicating the latest bound of the times of
            arrivals to count.
        route_tag: (Optional) String, tag identifying a route to filter the results by. If not
            specified, arrivals for all routes will be returned.
        stop_tag: (Optional) String, tag identifying a stop to filter the results by. If not
            specified, arrivals for all stops will be returned.

    Returns:
        A JSON response containing an array of objects for each pair of minutes away from the
        scheduled time and the number of arrivals at that time, with the following keys:
            minutes: Integer, the number of minutes away from their scheduled arrival time the
                arrivals are. Negative values are early arrivals, positive values are late arrivals,
                and 0 is on time arrivals.
            count: Integer, the count of the number of arrivals that are this many minutes away from
                their scheduled arrival time.
    """

    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    route_tag = request.GET.get('route_tag')
    stop_tag = request.GET.get('stop_tag')

    validation_errors = {}

    if start_time is None:
        validation_errors['start_time'] = 'start_time is required'

    try:
        start_time = validators.validate_timestamp(timestamp=start_time,
                                                   min_time=0)
    except ValidationError as e:
        validation_errors['start_time'] = e.messages[0]

    if end_time is not None:
        try:
            end_time = validators.validate_timestamp(timestamp=end_time,
                                                     min_time=start_time if isinstance(start_time, int) else 0)
        except ValidationError as e:
            validation_errors['end_time'] = e.messages[0]

    if route_tag is not None:
        try:
            route_tag = validators.validate_route_tag(route_tag=route_tag)
        except ValidationError as e:
            validation_errors['route_tag'] = e.messages[0]

    if stop_tag is not None:
        try:
            stop_tag = validators.validate_stop_tag(stop_tag=stop_tag)
        except ValidationError as e:
            validation_errors['stop_tag'] = e.message[0]

    if validation_errors:
        return JsonResponse(data=validation_errors,
                            status=400)

    arrivals = Arrival.objects.values(minutes=Func(F('difference') / 60, 0, function='TRUNCATE'))\
                              .annotate(count=Count('minutes'))\
                              .order_by('minutes')

    if route_tag is not None:
        arrivals = arrivals.filter(scheduled_arrival__stop_schedule_class__schedule_class__route__tag=route_tag)

    if stop_tag is not None:
        arrivals = arrivals.filter(scheduled_arrival__stop_schedule_class__stop__tag=stop_tag)

    if start_time is not None:
        arrivals = arrivals.filter(time__gte=start_time)

    if end_time is not None:
        arrivals = arrivals.filter(time__lte=end_time)

    return JsonResponse(data=list(arrivals),
                        status=200,
                        safe=False)
