import json
import logging
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)

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

def nextbus_request(url, params):
    """Make a request to the NextBus API, and return the JSON response.

    Arguments:
        url: String, the NextBus API URL to make the request to.
        params: Dictionary containing the query parameters to include with the request.

    Returns:
        Dictionary containing the JSON response returned by the request.
    """

    full_url = '%s?%s' % (url, urllib.parse.urlencode(params))
    request = urllib.request.Request(url=full_url,
                                     headers={
                                         'Accept-Encoding': 'gzip, deflate'
                                     },
                                     method='GET')

    try:
        log.info('Making request to URL %s', full_url)
        with urllib.request.urlopen(request) as response:
            response_text = response.read()
            json_response = json.loads(response_text)
    except urllib.error.HTTPError as e:
        error_msg = 'Request returned status %s due to reason: %s' % (e.code, e.reason)
        log.critical(error_msg)
        raise e
    except Exception as e:
        error_msg = 'Request failed due to exception: %s\nRequest response: %s' % (e, response_text)
        log.critical(error_msg)
        raise e
    else:
        return json_response
