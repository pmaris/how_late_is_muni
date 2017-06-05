"""Command for updating the routes stored in the database. This is done by making a request to the
Nextbus API using the routeList command for the transit agencey specified in the config.ini file,
and then every route returned is added to the datbase if it doesn't already exist in the database,
or the title of the route is updated if it already does exist.
"""

from django.core.management.base import BaseCommand, CommandError

import configparser
import json
import logging
import os.path as path
import urllib.error
import urllib.parse
import urllib.request

from worker.models import Route

log = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read(path.join(path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__))))),
            'config.ini'))

class Command(BaseCommand):
    help = 'Update routes stored in the database'

    def handle(self, *args, **options):
        # Assemble URL and prepare request
        params = urllib.parse.urlencode({
            'command': 'routeList',
            'a': config.get('nextbus', 'agency')
        })
        full_url = '%s?%s' % (config.get('nextbus', 'api_url'), params)
        request = urllib.request.Request(url=full_url,
                                         headers={'Accept-Encoding': 'gzip, deflate'},
                                         method='GET')

        try:
            log.info('Making get route list request to URL %s', full_url)
            with urllib.request.urlopen(request) as response:
                response_text = response.read()
                json_response = json.loads(response_text)
        except urllib.error.HTTPError as e:
            error_msg = 'Request returned status %s due to reason: %s' % (e.code, e.reason)
            log.critical(error_msg)
            raise CommandError(error_msg)
        except Exception as e:
            error_msg = 'Request failed due to exception: %s\nRequest response: %s' % (e, response_text)
            log.critical(error_msg)
            raise CommandError(error_msg)
        else:
            if 'route' in json_response:
                log.info('Adding routes to database')
                for route in json_response['route']:
                    new_route, created = \
                        Route.objects.update_or_create(defaults={
                                                           'tag': route['tag'],
                                                           'title': route['title']
                                                       },
                                                       tag=route['tag'])
                    if created:
                        log.debug('Added route %s to database', new_route.title)
                    else:
                        log.debug('Updated route %s in database', new_route.title)
            else:
                error_msg = 'Response body from get route list request did not include routes. ' \
                            'Response body: %s' % json_response
                log.critical(error_msg)
                raise CommandError(error_msg)
