# -*- coding: utf-8 -*-
from max.exceptions import ConnectionError
from max.exceptions.http import JSONHTTPInternalServerError
from max.exceptions.http import JSONHTTPServiceUnavailable
from max.exceptions.scavenger import format_raw_request, format_raw_response

from pymongo.errors import AutoReconnect
from pymongo.errors import ConnectionFailure

import logging
import signal

logger = logging.getLogger('exceptions')
request_logger = logging.getLogger('requestdump')
dump_requests = {'enabled': False}


def set_signal():
    def toggle_request_dump(*args):
        dump_requests['enabled'] = not dump_requests['enabled']
        request_logger.debug('{}abling request dumper'.format('En' if dump_requests['enabled'] else 'Dis'))

    signal.signal(signal.SIGUSR1, toggle_request_dump)


def catch_exception(request, e):
    if isinstance(e, ConnectionFailure):
        return JSONHTTPInternalServerError(error=dict(objectType='error', error='DatabaseConnectionError', error_description='Please try again later.'))
    elif isinstance(e, ConnectionError):
        return JSONHTTPServiceUnavailable(error=dict(objectType='error', error=ConnectionError.__name__, error_description=e.message))

SEPARATOR = '-' * 80
DUMP_TEMPLATE = """
{sep}
{{}}

--

{{}}
{sep}
""".format(sep=SEPARATOR)


def dump_request(request, response):
    """
        Logs formatted request + response to request_dump logger
        if global var dump_requests['enabled'] is True
    """
    if dump_requests['enabled'] and response.status_int != 500:
        request_logger.debug(DUMP_TEMPLATE.format(
            format_raw_request(request),
            format_raw_response(response)
        ))


def MaxResponse(fun):
    def replacement(context, request, *args, **kwargs):
        """
            Handle exceptions throwed in the process of executing the REST method and
            issue proper status code with message
        """
        # response = fun(*args, **kwargs)
        # return response
        try:
            response = fun(context, request, *args, **kwargs)
        except AutoReconnect:
            tryin_to_reconnect = True
            while tryin_to_reconnect:
                try:
                    response = fun(*args, **kwargs)
                except AutoReconnect:
                    pass
                except Exception, e:
                    response = catch_exception(request, e)
                    dump_request(request, response)
                    return response
                else:
                    tryin_to_reconnect = False
        except Exception, e:
            response = catch_exception(request, e)
            dump_request(request, response)
            return response
        else:
            # Don't cache by default, get configuration from resource if any
            route_cache_settings = RESOURCES.get(request.matched_route.name, {}).get('cache', 'must-revalidate, max-age=0, no-cache, no-store')
            response.headers.update({'Cache-Control': route_cache_settings})
            dump_request(request, response)
            return response
    replacement.__name__ = fun.__name__
    replacement.__doc__ = fun.__doc__

    return replacement
