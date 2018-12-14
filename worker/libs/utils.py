import datetime

from django.db import connection
from psqlextra.query import ConflictAction
from psqlextra.util import postgres_manager

def bulk_upsert(model, data, update_on_conflict, conflict_columns):
    """Perform a bulk upsert for a single database model that can either update
    or ignore entries that conflict with existing rows in the database.

    Arguments:
        model: (django.db.models.Model) The database model to perform the insert
            on.
        data: (List of dictionaries) The data to insert into the database. Each
            dictionary must have keys matching the name of a field on the
            database model with the values being the data to add for that
            column. All of the dictionaries must have the same keys.
        update_on_conflict: (Boolean) Indicates whether rows where a conflict
            occurs should be updated or not.
        conflict_columns: (List of strings) Names of the columns/fields on the
            model with unique constraints to be the columns part of the
            ON CONFLICT cause.
    """

    if update_on_conflict:
        conflict_action = ConflictAction.UPDATE
    else:
        conflict_action = ConflictAction.NOTHING

    with postgres_manager(model) as manager:
        manager.on_conflict(conflict_columns, conflict_action).bulk_insert(data)

def ensure_is_list(value):
    """Guarantee that a given value is returned as a list. If the value is not a list, a list
    containing the provided value as its only item is returned. If the value is already a list, it
    is returned unmodified. This is not the same behavior as calling list() on the value.

    Useful for fields in the NextBus API that can return either a JSON array or JSON object depening
    on whether there is one or multiple objects.

    Arguments:
        value: The value to return as a list.

    Returns:
        A list that is either the unmodified provided value, if it was a list, or a list that
        contains the provided value as its only item, if it was not a list.
    """

    if isinstance(value, list):
        return value
    else:
        return [value]

def get_current_service_class():
    """Get the service class for the current day/

    Returns:
        String, the service class for the current day. "wkd" if the current day is a weekday, "sat"
        if the current day is Saturday, and "sun" if the current day is Sunday.
    """

    current_day = datetime.datetime.now().strftime('%A').lower()

    if current_day == 'saturday':
        return 'sat'
    elif current_day == 'sunday':
        return 'sun'
    else:
        return 'wkd'

def get_seconds_since_midnight():
    """Get the number of seconds that have elapsed since midnight of the current day.

    Returns:
        Integer, the number of seconds that have elapsed since midnight of the current day.
    """

    current_time = datetime.datetime.now().timetuple()
    return (current_time.tm_hour * 60 * 60) + (current_time.tm_min * 60) + current_time.tm_sec
