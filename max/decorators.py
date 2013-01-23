# -*- coding: utf-8 -*-
from max.exceptions import MissingField, ObjectNotSupported, ObjectNotFound, DuplicatedItemError, UnknownUserError, Unauthorized, InvalidSearchParams, InvalidPermission, ValidationError
from max.exceptions import JSONHTTPUnauthorized, JSONHTTPBadRequest, JSONHTTPNotFound
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
    return mmdb.users.getItemsByusername(username)


def getContextActor(db, hash):
    mmdb = MADMaxDB(db)
    context = mmdb.contexts.getItemsByhash(hash)
    return context


def require_person_actor(exists=True):
    def wrap(view_function):
        def new_function(*args, **kw):
            nkargs = [a for a in args]
            context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])

            # Get user from Oauth headers
            username = getUsernameFromXOAuth(request)

            if not username:
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
                    actor = getUserActor(context.db, username)[0]
                except:
                    raise UnknownUserError('Unknown actor identified by username: %s' % username)

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


def require_context_actor(exists=True):
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
                    actor = getContextActor(context.db, contexthash)[0]
                except:
                    raise UnknownUserError('Unknown actor identified by context : %s' % contexthash)
                else:
                    #Only Uri contexts are allowed as actors
                    if actor.object['objectType'].lower() not in ['uri']:
                        raise ObjectNotSupported('%s objectType not supported as an actor' % actor.object['objectType'])

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


def MaxRequest(func):
    def replacement(*args, **kwargs):
        nkargs = [a for a in args]
        context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])

        actor = None
        admin_ws = [('admin_users', 'GET'), ('admin_activities', 'GET'), ('admin_contexts', 'GET'), ('admin_user', 'DELETE'), ('admin_activity', 'DELETE'), ('admin_context', 'DELETE')]
        allowed_ws_without_username = admin_ws + [('contexts', 'POST'), ('context', 'GET'), ('context', 'PUT'), ('context', 'DELETE')]
        allowed_ws_without_actor = [('user', 'POST')] + allowed_ws_without_username

        # If Oauth authorization is used, The actor that will perform the actions will be
        # the one specified in oauth headers, so for routes that match username
        # parameter in the URI, we only allow this username to be the same as oauth username
        # for validation purposes. Same thing from actor defined in post request body
        if isOauth(request):
            oauth_username = getUsernameFromXOAuth(request)
            rest_username = getUsernameFromURI(request)

            # XXX TODO Define cases where oauth_username MAY/CAN be different
            # to rest_username/post_username
            if rest_username and oauth_username != rest_username:
                raise Unauthorized("You don't have permission to access %s resources" % (rest_username))
            post_username = getUsernameFromPOSTBody(request)
            if post_username and oauth_username != post_username:
                raise Unauthorized("You don't have permission to access %s resources" % (post_username))
            # If user validation is successfull, try to load the oauth User from DB
            try:
                actor = getUserActor(context.db, oauth_username)[0]
            except:
                raise UnknownUserError('Unknown user "%s"' % oauth_username)

        # If Basic auth is used, actor username can be any username, as we are
        # impersonating him. We will search for this username in several places:

        elif isBasic(request):
            actorType = 'person'
            #Try to get the username from the REST URI
            username = getUsernameFromURI(request)
            #Try to get the username from the POST body
            if not username and request.method == 'POST':
                username = getUsernameFromPOSTBody(request)

            # If no actor specified anywhere, raise an error)
            # except when allowed not having a username
            # or when adding a context activity
            if not username:
                if (request.matched_route.name, request.method) == ('admin_context_activities', 'POST'):
                    contexthash = getUrlHashFromURI(request)
                    actorType = 'context'
                elif not ((request.matched_route.name, request.method) in allowed_ws_without_username):
                    raise UnknownUserError('No user specified as actor')

            # Raise only if we are NOT adding a user or a context. These are the only cases
            # Were we permit not specifing an ator:
            #   - Creating a user, beacause the user doesn't exists
            #   - Creating a context, because context is actor-agnostic
            #   - Getting a context, because context is actor-agnostic

            #try to load the user actor from DB
            if actorType == 'person':
                try:
                    actor = getUserActor(context.db, username)[0]
                except:
                    if not ((request.matched_route.name, request.method) in allowed_ws_without_actor):
                        raise UnknownUserError('Unknown actor identified by username: %s' % username)

            #try to load the context actor from DB
            if actorType == 'context':
                try:
                    actor = getContextActor(context.db, contexthash)[0]
                except:
                    raise UnknownUserError('Unknown actor identified by context : %s' % contexthash)
                else:
                    #Only Uri contexts are allowed as actors
                    if actor.object['objectType'].lower() not in ['uri']:
                        raise ObjectNotSupported('%s objectType not supported as an actor' % actor.object['objectType'])

        # Raise an error if no authentication present
        else:
            raise Unauthorized("There are no supported authentication methods present in this request")

        # If we arrive at this point, we have a valid user in actor.
        # (Except in the case of a new users explained 10 lines up)
        # Define a callable to prepare the actor in order to inject it in the request
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

        response = func(*args, **kwargs)
        return response
    return replacement


def MaxResponse(fun):
    def replacement(*args, **kwargs):
        # Handle exceptions throwed in the process of executing the REST method and
        # issue proper status code with message
        nkargs = [a for a in args]
        context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])
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
