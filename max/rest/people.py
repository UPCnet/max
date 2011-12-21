from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError, HTTPNotImplemented

from max.exceptions import MissingField
from max.MADMax import MADMaxDB, MADMaxCollection
from max.models import User
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity


@view_config(route_name='users', request_method='GET')
def getUsers(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    users = mmdb.users.dump(flatten=1)
    handler = JSONResourceRoot(users)
    return handler.buildResponse()


@view_config(route_name='user', request_method='GET')
def getUser(context, request):
    """
    """
    displayName = request.matchdict['displayName']

    users = MADMaxCollection(context.db.users, query_key='displayName')
    user = users[displayName].flatten()

    handler = JSONResourceEntity(user)
    return handler.buildResponse()


@view_config(route_name='user', request_method='POST')
def addUser(context, request):
    """
    """
    displayName = request.matchdict['displayName']
    rest_params = {'displayName': displayName}

    # Try to initialize a User object from the request
    # And catch the possible exceptions
    try:
        newuser = User(request, rest_params=rest_params)
    except MissingField:
        return HTTPBadRequest()
    except ValueError:
        return HTTPBadRequest()
    except:
        return HTTPInternalServerError()

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newuser.get('_id'):
        # Already Exists
        code = 200
    else:
        # New User
        code = 201
        userid = newuser.insert()
        newuser['_id'] = userid

    handler = JSONResourceEntity(newuser.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='user', request_method='PUT')
def ModifyUser(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='user', request_method='DELETE')
def DeleteUser(context, request):
    """
    """
    return HTTPNotImplemented()
