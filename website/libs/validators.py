"""Reusable validators for parameters in API requests."""

from django.core.exceptions import ValidationError
from worker.models import Route, Stop

def validate_boolean(value):
    """Validate whether a value is a valid boolean.

    Arguments:
        value: The value to validate. This can be a boolean value, the string "true", "false", "t",
            or "f" (Case-insensitive), or the integers 0 or 1.

    Returns:
        Boolean, the validated boolean value.

    Raises:
        django.core.exceptions.ValidationError: If the value isn't a valid boolean.
    """

    if isinstance(value, bool):
        return value
    elif str(value).lower() in ['true', 't', '1']:
        return True
    elif str(value).lower() in ['false', 'f', '0']:
        return False
    else:
        raise ValidationError(message='Invalid boolean value: %(value)s',
                              params={'value': value})

def validate_choice(value, valid_choices):
    """Validate whether a value is in a list of choices.

    Arguments:
        value: The value to validate.
        valid_choices: (List) The possible valid choices for the value.

    Returns:
        The provided value.

    Raises:
        django.core.exceptions.ValidationError: If the value isn't in the list of valid choices.
    """

    if value in valid_choices:
        return value
    else:
        raise ValidationError(message='Invalid value %(value)s, valid values are: %(valid_choices)s',
                              params={'value': value,
                                      'valid_choices': valid_choices})

def validate_route_tag(route_tag):
    """Validate whether a route exists in the database with a specified route tag.

    Arguments:
        route_tag: String, a route tag identifying a route in the database.

    Returns:
        String, the validated route tag.

    Raises:
        django.core.exceptions.ValidationError: If the route_tag is invalid.
    """

    route_tag = str(route_tag)
    try:
        route = Route.objects.get(tag=route_tag)
    except Route.DoesNotExist:
        raise ValidationError(message='Route with tag %(route_tag)s does not exist',
                              params={'route_tag': route_tag})
    else:
        return route_tag

def validate_stop_tag(stop_tag):
    """Validate whether a stop exists in the database with a specified stop tag.

    Arguments:
        stop_tag: String, a stop tag identifying a stop in the database.

    Returns:
        String, the validated stop tag.

    Raises:
        django.core.exceptions.ValidationError: If the stop_tag is invalid.
    """

    stop_tag = str(stop_tag)
    try:
        stop = Stop.objects.get(tag=stop_tag)
    except Stop.DoesNotExist:
        raise ValidationError(message='Stop with tag %(stop_tag)s does not exist',
                              params={'stop_tag': stop_tag})
    else:
        return stop_tag

def validate_timestamp(timestamp, min_time=0):
    """Validate a Unix timestamp.

    Arguments:
        timestamp: A Unix timestamp. The value provided will be cast to an integer.
        min_time: Integer, the minimum allowed timestamp.

    Returns:
        Integer, the validated timestamp.

    Raises:
        django.core.exceptions.ValidationError: If the timestamp is invalid.
    """

    try:
        timestamp = int(timestamp)
    except (TypeError, ValueError):
        raise ValidationError(message='An integer is required')
    else:
        if timestamp < min_time:
            raise ValidationError(message='Timestamp must be greater than or equal to %(min_time)s',
                                  params={'min_time': min_time})

        return timestamp
