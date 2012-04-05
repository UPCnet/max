from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented
from pyramid.response import Response

from max.MADMax import MADMaxDB, MADMaxCollection
from max.models import User
from max.decorators import MaxRequest, MaxResponse
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
import os

from max.oauth2 import oauth2
from max.rest.utils import extractPostData


@view_config(route_name='user', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getUser(context, request):
    """
    """
    handler = JSONResourceEntity(request.actor.flatten())
    return handler.buildResponse()


@view_config(route_name='user', request_method='POST', permission='operations')
@MaxResponse
@MaxRequest
def addUser(context, request):
    """
    """
    username = request.matchdict['username']
    rest_params = {'username': username}

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
    AVATAR_FOLDER = request.registry.settings.get('avatar_folder')
    username = request.matchdict['username']
    filename = os.path.exists('%s/%s.jpg' % (AVATAR_FOLDER, username)) and username or 'missing'
    data = open('%s/%s.jpg' % (AVATAR_FOLDER, filename)).read()
    image = Response(data, status_int=200)
    image.content_type = 'image/jpeg'
    return image


@view_config(route_name='user', request_method='PUT')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def ModifyUser(context, request):
    """
    """
    actor = request.actor
    params = extractPostData(request)
    allowed_fields = [fieldName for fieldName in actor.schema if actor.schema[fieldName].get('user_mutable', 0)]
    properties = {fieldName: params.get(fieldName) for fieldName in allowed_fields if params.get(fieldName, None)}
    actor.modifyUser(properties)

    users = MADMaxCollection(context.db.users, query_key='username')
    handler = JSONResourceEntity(users[actor['username']].flatten())
    return handler.buildResponse()


@view_config(route_name='user', request_method='DELETE')
def DeleteUser(context, request):
    """
    """
    return HTTPNotImplemented()
