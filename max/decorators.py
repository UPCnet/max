# -*- coding: utf-8 -*-
from max.MADMax import MADMaxDB
from max.exceptions import ConnectionError
from max.exceptions import ObjectNotSupported
from max.exceptions import Unauthorized
from max.exceptions import UnknownUserError
from max.exceptions.http import JSONHTTPInternalServerError
from max.exceptions.http import JSONHTTPServiceUnavailable
from max.rest.resources import RESOURCES
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


def getUserActor(db, username):
    mmdb = MADMaxDB(db)
    actor = mmdb.users.getItemsByusername(username)[0]
    return actor


def getContextActor(db, hash):
    mmdb = MADMaxDB(db)
    context = mmdb.contexts.getItemsByhash(hash)[0]
    return context


def requirePersonActor(exists=True, force_own=True):
    """
        Requires the actor provided in the request to be of type Person.

        exists:    Actor username must match an existing user on DB
        force_own: Actor username must match the username provided in auhentication
    """
    def wrap(view_function):
        def new_function(context, request, *args, **kw):
            # Get user from Oauth headers
            oauth_username = getUsernameFromXOAuth(request)
            username = str(oauth_username)  # To avoid variable reference

            # If we have a username in the URI, take it
            uri_username = getUsernameFromURI(request)
            if uri_username:
                username = uri_username.lower()

            # If we have a username in a POST body, take it
            if request.method in ['POST', 'PUT']:
                post_username = getUsernameFromPOSTBody(request)
                if post_username:
                    username = post_username.lower()

            # Check a valid actor exists in the tdatabase
            if exists:
                try:
                    actor = getUserActor(context.db, username)
                except IndexError:
                    raise UnknownUserError('Unknown actor identified by username: %s' % username)

            if force_own:
                if username != oauth_username:
                    raise Unauthorized("You don't have permission to access %s resources" % (username))

            def getActor(request):
                try:
                    actor.setdefault('displayName', actor['username'])
                    return actor
                except:
                    return None

            request.set_property(getActor, name='actor', reify=True)

            return view_function(context, request, *args, **kw)

        new_function.__doc__ = view_function.__doc__
        new_function.__name__ = view_function.__name__
        return new_function
    try:
        wrap.__name__ = wrap.func_closure[1].cell_contents.__name__
        wrap.__doc__ = wrap.func_closure[1].cell_contents.__doc__
    except:
        pass
    if type(exists) == type(wrap):
        return wrap(exists)
    return wrap


def requireContextActor(exists=True):
    """
        Requires the actor provided in the request to be of type Context.

        exists:    Actor context must match an existing context on DB
    """
    def wrap(view_function):
        def new_function(context, request, *args, **kw):
            # check we have a hash in the uri
            contexthash = getUrlHashFromURI(request)
            if not contexthash:
                raise UnknownUserError('No context specified as actor')

            # Check a valid context exists in the tdatabase
            if exists:
                try:
                    actor = getContextActor(context.db, contexthash)
                except IndexError:
                    raise UnknownUserError('Unknown actor identified by context : %s' % contexthash)
                else:
                    # Only ontexts are allowed as context actors
                    if actor['objectType'].lower() not in ['context']:
                        raise ObjectNotSupported('%s objectType not supported as an actor' % actor['objectType'])

            def getActor(request):
                try:
                    actor.setdefault('displayName', actor['url'])
                    return actor
                except:
                    return None

            request.set_property(getActor, name='actor', reify=True)

            return view_function(context, request, *args, **kw)

        new_function.__doc__ = view_function.__doc__
        new_function.__name__ = view_function.__name__
        return new_function
    try:
        wrap.__name__ = wrap.func_closure[1].cell_contents.__name__
        wrap.__doc__ = wrap.func_closure[1].cell_contents.__doc__
    except:
        pass
    if type(exists) == type(wrap):
        return wrap(exists)
    return wrap


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
