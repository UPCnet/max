from max.exceptions import MissingField, ObjectNotSupported, MongoDBObjectNotFound, DuplicatedItemError, UnknownUserError, Unauthorized, InvalidSearchParams
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError, HTTPUnauthorized
from bson.errors import InvalidId
from max.resources import Root

def MaxRequest(func):
    def replacement(*args, **kwargs):
        nkargs = [a for a in args]
        context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])
        #import ipdb;ipdb.set_trace()
        response = func(*args, **kwargs)
        return response
    return replacement


def MaxResponse(func):
    def replacement(*args, **kwargs):
        # Handle exceptions throwed in the process of executing the REST method and
        # issue proper status code with message
        try:
            response = func(*args, **kwargs)
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
            return response
    return replacement
