from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented
from pyramid.response import Response

from max.MADMax import MADMaxDB, MADMaxCollection
from max.models import User
from max.decorators import MaxRequest, MaxResponse
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
import os

from max.oauth2 import oauth2


@view_config(route_name='users', request_method='GET')
@MaxResponse
@MaxRequest
def getUsers(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    users = mmdb.users.dump(flatten=1)
    handler = JSONResourceRoot(users)
    return handler.buildResponse()


@view_config(route_name='user', request_method='GET')
@MaxResponse
@MaxRequest
def getUser(context, request):
    """
    """
    displayName = request.matchdict['displayName']

    users = MADMaxCollection(context.db.users, query_key='displayName')
    user = users[displayName].flatten()

    handler = JSONResourceEntity(user)
    return handler.buildResponse()


@view_config(route_name='user', request_method='POST')
@MaxResponse
@MaxRequest
def addUser(context, request):
    """
    """
    displayName = request.matchdict['displayName']
    rest_params = {'displayName': displayName}

    # Initialize a User object from the request
    newuser = User(request, rest_params=rest_params)

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


@view_config(route_name='avatar', request_method='GET')
def getUserAvatar(context, request):
    """
    """
    AVATAR_FOLDER = '/var/pyramid/max/avatars'
    displayName = request.matchdict['displayName']
    filename = os.path.exists('%s/%s.jpg' % (AVATAR_FOLDER, displayName)) and displayName or 'missing'
    data = open('%s/%s.jpg' % (AVATAR_FOLDER, filename)).read()
    image = Response(data, status_int=200)
    image.content_type = 'image/jpeg'
    return image


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
