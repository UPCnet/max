# -*- coding: utf-8 -*-
from max.exceptions import MissingField, ObjectNotSupported, ObjectNotFound, DuplicatedItemError, UnknownUserError, Unauthorized, InvalidSearchParams, InvalidPermission, ValidationError, Forbidden
from max.exceptions import JSONHTTPUnauthorized, JSONHTTPBadRequest, JSONHTTPNotFound, JSONHTTPForbidden
from pyramid.httpexceptions import HTTPInternalServerError
from bson.errors import InvalidId
from max.MADMax import MADMaxDB
from max.resources import Root
from max.rest.resources import RESOURCES
from max.rest.utils import isOauth, isBasic, getUsernameFromXOAuth, getUsernameFromURI, getUsernameFromPOSTBody, getUrlHashFromURI
from max.models import User, Context
from beaker.cache import cache_region, Cache


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

            if not oauth_username:
                # Something went really, really wrong, because when we get here, we shoud
                # have succesfully passed OAuth authentication
                raise Unauthorized("Invalid Authentication")

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
                    raise Unauthorized("You don't have permission to access %s resources" % (oauth_username))

            def getActor(request):
                try:
                    if isinstance(actor, User):
                        actor.setdefault('displayName', actor['username'])
                    if isinstance(actor, Context):
                        actor.setdefault('displayName', actor['object']['url'])
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
                    if isinstance(actor, User):
                        actor.setdefault('displayName', actor['username'])
                    if isinstance(actor, Context):
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
        except InvalidId, message:
            return JSONHTTPBadRequest(error=dict(error=InvalidId.__name__, error_description=message.value))
        except ObjectNotSupported, message:
            return JSONHTTPBadRequest(error=dict(error=ObjectNotSupported.__name__, error_description=message.value))
        except ObjectNotFound, message:
            return JSONHTTPNotFound(error=dict(error=ObjectNotFound.__name__, error_description=message.value))
        except MissingField, message:
            return JSONHTTPBadRequest(error=dict(error=MissingField.__name__, error_description=message.value))
        except DuplicatedItemError, message:
            return JSONHTTPBadRequest(error=dict(error=DuplicatedItemError.__name__, error_description=message.value))
        except UnknownUserError, message:
            return JSONHTTPBadRequest(error=dict(error=UnknownUserError.__name__, error_description=message.value))
        except Unauthorized, message:
            return JSONHTTPUnauthorized(error=dict(error=Unauthorized.__name__, error_description=message.value))
        except InvalidSearchParams, message:
            return JSONHTTPBadRequest(error=dict(error=InvalidSearchParams.__name__, error_description=message.value))
        except InvalidPermission, message:
            return JSONHTTPBadRequest(error=dict(error=InvalidPermission.__name__, error_description=message.value))
        except ValidationError, message:
            return JSONHTTPBadRequest(error=dict(error=ValidationError.__name__, error_description=message.value))
        except Forbidden, message:
            return JSONHTTPForbidden(error=dict(error=Forbidden.__name__, error_description=message.value))

        # JSON decode error????
        except ValueError:
            return JSONHTTPBadRequest(error=dict(error='JSONDecodeError', error_description='Invalid JSON data found on requests body'))
        except:
            return HTTPInternalServerError()
        else:
            try:
                # Don't cache by default, get configuration from resource if any
                route_cache_settings = RESOURCES.get(request.matched_route.name).get('cache', 'must-revalidate, max-age=0, no-cache, no-store')
                response.headers.update({'Cache-Control': route_cache_settings})
            except:
                pass
            return response
    return replacement
