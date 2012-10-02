# -*- coding: utf-8 -*-
import os
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented
from pyramid.response import Response

from max.models import User
from max.oauth2 import oauth2
from max.MADMax import MADMaxDB
from max.rest.utils import searchParams
from max.decorators import MaxRequest, MaxResponse
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity


@view_config(route_name='users', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getUsers(context, request):
    """
         /people

         Retorna tots els users
    """
    mmdb = MADMaxDB(context.db)
    query = {}
    users = mmdb.users.search(query, sort="username", flatten=1, **searchParams(request))

    handler = JSONResourceRoot(users)
    return handler.buildResponse()


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
    newuser = User()
    newuser.fromRequest(request, rest_params=rest_params)

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
    properties = actor.getMutablePropertiesFromRequest(request, mutable_permission="user_mutable")
    actor.modifyUser(properties)
    handler = JSONResourceEntity(actor.flatten())
    return handler.buildResponse()


@view_config(route_name='user', request_method='DELETE')
def DeleteUser(context, request):
    """
    """
    return HTTPNotImplemented()
