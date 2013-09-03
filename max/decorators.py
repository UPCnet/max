# -*- coding: utf-8 -*-
from max.exceptions import MissingField, ObjectNotSupported, ObjectNotFound, DuplicatedItemError, UnknownUserError, Unauthorized, InvalidSearchParams, InvalidPermission, ValidationError, Forbidden
from max.exceptions import JSONHTTPUnauthorized, JSONHTTPBadRequest, JSONHTTPNotFound, JSONHTTPForbidden, JSONHTTPInternalServerError
from bson.errors import InvalidId
from max.MADMax import MADMaxDB
from max.resources import Root
from max.rest.resources import RESOURCES
from max.rest.utils import getUsernameFromXOAuth, getUsernameFromURI, getUsernameFromPOSTBody, getUrlHashFromURI
from max.models import User, Context

from pymongo.errors import AutoReconnect
from pymongo.errors import ConnectionFailure

import traceback
from datetime import datetime
import json
from hashlib import sha1
import logging
logger = logging.getLogger('exceptions')
from pyramid.settings import asbool


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
        def new_function(*args, **kw):
            nkargs = [a for a in args]
            context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])

            # Get user from Oauth headers
            oauth_username = getUsernameFromXOAuth(request)
            username = str(oauth_username)  # To avoid variable reference

            # If we have a username in the URI, take it
            uri_username = getUsernameFromURI(request)
            if uri_username:
                username = uri_username

            # If we have a username in a POST body, take it
            if request.method == 'POST':
                post_username = getUsernameFromPOSTBody(request)
                if post_username:
                    username = post_username

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

            return view_function(*args, **kw)

        new_function.__doc__ = view_function.__doc__
        return new_function
    if type(exists) == type(wrap):
        return wrap(exists)
    return wrap


def requireContextActor(exists=True):
    """
        Requires the actor provided in the request to be of type Context.

        exists:    Actor context must match an existing context on DB
    """
    def wrap(view_function):
        def new_function(*args, **kw):
            nkargs = [a for a in args]
            context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])

            #check we have a hash in the uri
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
                    #Only ontexts are allowed as context actors
                    if actor['objectType'].lower() not in ['context']:
                        raise ObjectNotSupported('%s objectType not supported as an actor' % actor['objectType'])

            def getActor(request):
                try:
                    actor.setdefault('displayName', actor['url'])
                    return actor
                except:
                    return None

            request.set_property(getActor, name='actor', reify=True)

            return view_function(*args, **kw)

        new_function.__doc__ = view_function.__doc__
        return new_function
    if type(exists) == type(wrap):
        return wrap(exists)
    return wrap

ERROR_TEMPLATE = """
------------------------------------------------
BEGIN EXCEPTION REPORT: {hash}
DATE: {time}
REQUEST:

{raw_request}

TRACEBACK:

{traceback}

END EXCEPTION REPORT
------------------------------------------------
"""


def saveException(request, error):  # pragma: no cover
    """
        Logs the exception

        This code will only raise if a non-tested thing appear
         So, as the tests will not ever see this, we exlcude it from coverage
    """
    time = datetime.now().isoformat()
    entry = dict(
        traceback=error,
        time=time,
        raw_request=request.as_string(),
        matched_route=request.matched_route.name,
        matchdict=request.matchdict,
    )
    dump = json.dumps(entry)
    entry['hash'] = sha1(dump).hexdigest()
    exception_log = ERROR_TEMPLATE.format(**entry)
    logger.debug(exception_log)
    return entry['hash'], exception_log


def catch_exception(request, e):
    if isinstance(e, ConnectionFailure):
        return JSONHTTPInternalServerError(error=dict(error='DatabaseConnectionError', error_description='Please try again later.'))
    elif isinstance(e, InvalidId):
        return JSONHTTPBadRequest(error=dict(error=InvalidId.__name__, error_description=e.value))
    elif isinstance(e, ObjectNotSupported):
        return JSONHTTPBadRequest(error=dict(error=ObjectNotSupported.__name__, error_description=e.value))
    elif isinstance(e, ObjectNotFound):
        return JSONHTTPNotFound(error=dict(error=ObjectNotFound.__name__, error_description=e.value))
    elif isinstance(e, MissingField):
        return JSONHTTPBadRequest(error=dict(error=MissingField.__name__, error_description=e.value))
    elif isinstance(e, DuplicatedItemError):
        return JSONHTTPBadRequest(error=dict(error=DuplicatedItemError.__name__, error_description=e.value))
    elif isinstance(e, UnknownUserError):
        return JSONHTTPBadRequest(error=dict(error=UnknownUserError.__name__, error_description=e.value))
    elif isinstance(e, Unauthorized):
        return JSONHTTPUnauthorized(error=dict(error=Unauthorized.__name__, error_description=e.value))
    elif isinstance(e, InvalidSearchParams):
        return JSONHTTPBadRequest(error=dict(error=InvalidSearchParams.__name__, error_description=e.value))
    elif isinstance(e, InvalidPermission):
        return JSONHTTPBadRequest(error=dict(error=InvalidPermission.__name__, error_description=e.value))
    elif isinstance(e, ValidationError):
        return JSONHTTPBadRequest(error=dict(error=ValidationError.__name__, error_description=e.value))
    elif isinstance(e, Forbidden):
        return JSONHTTPForbidden(error=dict(error=Forbidden.__name__, error_description=e.value))

    # JSON decode error????
    elif isinstance(e, ValueError):
        return JSONHTTPBadRequest(error=dict(error='JSONDecodeError', error_description='Invalid JSON data found on requests body'))
    # This code will only raise if a non-tested thing appear
    # So, as the tests will not ever see this, we exlcude it from coverage
    else:  # pragma: no cover
        error = traceback.format_exc()
        sha1_hash, log = saveException(request, error)
        max_server = request.environ.get('HTTP_X_VIRTUAL_HOST_URI', '')

        error_description = 'Your error has been logged at {}/exceptions/{}. Please contact the system admin.'.format(max_server, sha1_hash)
        if asbool(request.registry.settings.get('testing', False)):  # pragma: no cover
            error_description = 'An exception occurred. Below is the catched exception.\n\nSorry for the convenience.\n\n' + log.replace('\n', '\n    ')[:-4]

        return JSONHTTPInternalServerError(error=dict(error='ServerError', error_description=error_description))


def MaxResponse(fun):
    def replacement(*args, **kwargs):
        # Handle exceptions throwed in the process of executing the REST method and
        # issue proper status code with message
        nkargs = [a for a in args]
        context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])
        # response = fun(*args, **kwargs)
        # return response
        try:
            response = fun(*args, **kwargs)
        except AutoReconnect:
            tryin_to_reconnect = True
            while tryin_to_reconnect:
                try:
                    response = fun(*args, **kwargs)
                except AutoReconnect:
                    pass
                except Exception, e:
                    return catch_exception(request, e)
                else:
                    tryin_to_reconnect = False
        except Exception, e:
            return catch_exception(request, e)
        else:
            # Don't cache by default, get configuration from resource if any
            route_cache_settings = RESOURCES.get(request.matched_route.name, {}).get('cache', 'must-revalidate, max-age=0, no-cache, no-store')
            response.headers.update({'Cache-Control': route_cache_settings})
            return response
    return replacement
