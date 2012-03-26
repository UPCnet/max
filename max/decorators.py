from max.exceptions import MissingField, ObjectNotSupported, ObjectNotFound, DuplicatedItemError, UnknownUserError, Unauthorized, InvalidSearchParams, InvalidPermission
from max.exceptions import JSONHTTPUnauthorized, JSONHTTPBadRequest
from pyramid.httpexceptions import HTTPInternalServerError
from bson.errors import InvalidId
from max.MADMax import MADMaxDB
from max.resources import Root
from max.rest.resources import RESOURCES
from max.rest.utils import isOauth, isBasic, getUsernameFromXOAuth, getUsernameFromURI, getUsernameFromPOSTBody


def MaxRequest(func):
    def replacement(*args, **kwargs):
        nkargs = [a for a in args]
        context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])

        actor = None
        mmdb = MADMaxDB(context.db)

        allowed_ws_without_username = [('contexts', 'POST'), ('context', 'GET'), ('context', 'PUT'), ('context', 'DELETE')]
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
                raise Unauthorized, "You don't have permission to access %s resources" % (rest_username)
            post_username = getUsernameFromPOSTBody(request)
            if post_username and oauth_username != post_username:
                raise Unauthorized, "You don't have permission to access %s resources" % (post_username)
            # If user validation is successfull, try to load the oauth User from DB
            try:
                actor = mmdb.users.getItemsByusername(oauth_username)[0]
            except:
                raise UnknownUserError, 'Unknown user "%s"' % oauth_username

        # If Basic auth is used, actor username can be any username, as we are
        # impersonating him. We will search for this username in several places:

        elif isBasic(request):
            #Try to get the username from the REST URI
            username = getUsernameFromURI(request)
            #Try to get the username from the POST body
            if not username and request.method == 'POST':
                username = getUsernameFromPOSTBody(request)

            # If no actor specified anywhere, raise an error
            # except when adding or modifying a context
            if not username:
                if not ((request.matched_route.name, request.method) in allowed_ws_without_username):
                    raise UnknownUserError, 'No user specified as actor'
            #try to load the oauth User from DB
            try:
                actor = mmdb.users.getItemsByusername(username)[0]
            except:
                # Raise only if we are NOT adding a user or a context. These are the only cases
                # Were we permit not specifing an ator:
                #   - Creating a user, beacause the user doesn't exists
                #   - Creating a context, because context is actor-agnostic
                #   - Getting a context, because context is actor-agnostic

                if not ((request.matched_route.name, request.method) in allowed_ws_without_actor):
                    raise UnknownUserError, 'Unknown user: %s' % username

        # Raise an error if no authentication present
        else:
            raise Unauthorized, "There are no supported authentication methods present in this request"

        # If we arrive at this point, we have a valid user in actor.
        # (Except in the case of a new users explained 10 lines up)
        # Define a callable to prepare the actor in order to inject it in the request
        def getActor(request):
            try:
                actor.setdefault('displayName', actor['username'])
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
            return JSONHTTPBadRequest(error=dict(error=ObjectNotFound.__name__, error_description=message.value))
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
