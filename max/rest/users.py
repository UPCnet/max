from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk, HTTPNotFound, HTTPInternalServerError

import json
from pymongo.objectid import ObjectId

from max.resources import Root
from max.rest.utils import checkDataAddUser, checkRequestConsistency, extractPostData

from max.MADMax import MADMaxDB,MADMaxCollection
from max.models import User
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity

import datetime
       

@view_config(route_name='users', request_method='GET')
def UsersGetter(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    users = mmdb.users.dump()
    handler = JSONResourceRoot(users)
    return handler.buildResponse()

@view_config(route_name='user', request_method='GET')
def UserGetter(context, request):
    """
    """
    displayName = request.matchdict['user_displayName']

    users = MADMaxCollection(context.db.users,query_key='displayName')
    user = users[displayName]

    handler = JSONResourceEntity(user)
    return handler.buildResponse()

@view_config(route_name='user', request_method='POST')
def UserAdder(context, request):
    """
    """
    displayName = request.matchdict['user_displayName']

    newuser = User(request)
    userid = newuser.insert()

    handler = JSONResourceEntity(userid)
    return handler.buildResponse()

