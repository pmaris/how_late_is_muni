import datetime

from django.db import connection

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

def bulk_insert(table_name, column_names, data, update_columns=None, ignore_duplicates=False):
    """Perform a bulk insert into a table in the database with an ON DUPLICATE KEY UPDATE, which is
    not supported by Django's bulk_create method.

    Arguments:
        table_name: (String) Name of the database table to insert the data in to.
        column_names: (List of strings) List of names of the columns to insert values into.
        data: (Nested lists) List containing lists of each row of data to insert into the database,
            with the data for each column being in the same order as the names of the columns in the
            provided column_names list.
        update_columns: (List of strings) Names of the columns to update in the ON DUPLICATE KEY
            UPDATE clause. If this is None, the ON DUPLICATE KEY UPDATE clause will not be added to
            the SQL statement that is executed.
        ignore_duplicates: (Boolean) Indicates if the IGNORE modifier should be used to ignore
            errors that occur with the insert.
    """

    # Construct column names to insert the data into
    columns = ','.join(['`%s`' % column_name for column_name in column_names])

    # Construct the insert for a single row with the necessary number of parameters
    parameterized_row = '(%s)' % ','.join(['%s'] * len(column_names))

    # Construct parameterized inserts for each row of data to insert
    parameterized_rows = ','.join([parameterized_row] * len(data))

    # Construct the columns to update on the duplicate key condition
    if update_columns is not None:
        update_clause = 'ON DUPLICATE KEY UPDATE %s' % \
                        ','.join(['`%s`=VALUES(`%s`)' % (column, column) for column in update_columns])
    else:
        update_clause = ''

    if ignore_duplicates:
        insert_statement = 'INSERT IGNORE INTO '
    else:
        insert_statement = 'INSERT INTO '

    sql = '%s `%s` (%s) VALUES %s %s' % (insert_statement, table_name, columns, parameterized_rows,
                                         update_clause)
    params = [item for column in data for item in column]

    with connection.cursor() as cursor:
        cursor.execute(sql, params)

def get_current_service_class():
    """Get the service class for the current day/

    Returns:
        String, the service class for the current day. "wkd" if the current day is a weekday, "sat"
        if the current day is Saturday, and "sun" if the current day is Sunday.
    """

    current_day = datetime.datetime.now().strftime('%A')

    if current_day == 'Saturday':
        return 'sat'
    elif current_day == 'Sunday':
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
