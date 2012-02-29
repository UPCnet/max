from max.exceptions import MissingField, ObjectNotSupported, MongoDBObjectNotFound, DuplicatedItemError, UnknownUserError, Unauthorized, InvalidSearchParams
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError, HTTPUnauthorized
from bson.errors import InvalidId
from max.resources import Root
from max.rest.resources import RESOURCES


def MaxRequest(func):
    def replacement(*args, **kwargs):
        nkargs = [a for a in args]
        context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])
        #import ipdb;ipdb.set_trace()
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
            return HTTPBadRequest(detail=message)
        except ObjectNotSupported, message:
            return HTTPBadRequest(detail=message)
        except MongoDBObjectNotFound, message:
            return HTTPBadRequest(detail=message)
        except MissingField, message:
            return HTTPBadRequest(detail=message)
        except DuplicatedItemError, message:
            return HTTPBadRequest(detail=message)
        except UnknownUserError, message:
            return HTTPBadRequest(detail=message)
        except Unauthorized, message:
            return HTTPUnauthorized(detail=message)
        except InvalidSearchParams, message:
            return HTTPBadRequest(detail=message)

        # JSON decode error????
        except ValueError:
            return HTTPBadRequest()
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
