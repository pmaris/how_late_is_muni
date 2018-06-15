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
