from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk

import json
from bson import json_util
from pymongo.objectid import ObjectId

from max.resources import Root
from max.rest.utils import checkDataAddUser, checkRequestConsistency, extractPostData

from max.MADMax import MADMaxDB
from max.models import User

import datetime


@view_config(route_name='users', request_method='GET')
def UsersResourceRoot(context, request):
    """
         /users/

         Retorna tots els usuaris del sistema
    """
    mmdb = MADMaxDB(context.db)

    json_data = json.dumps(mmdb.users.dump(), default=json_util.default)
    response = Response(json_data)
    response.content_type = 'application/json'
    response.headers['Access-Control-Allow-Origin']='*'    


@view_config(route_name='user', request_method='GET')
def UsersResourceGetUser(context, request):
    displayName = request.matchdict['user_displayName']

    mmdb = MADMaxDB(context.db)
    user = mmdb.users.getItemsBydisplayName(displayName)

    json_data = json.dumps(user, default=json_util.default)
    response = Response(json_data)
    response.content_type = 'application/json'
    response.headers['Access-Control-Allow-Origin']='*'    
    return response

@view_config(route_name='user', request_method='POST')
def UsersResourceAddUser(context, request):
    displayName = request.matchdict['user_displayName']

    newuser = User(request)
    userid = newuser.insert()

    json_data = json.dumps(userid, default=json_util.default)
    response = Response(json_data)
    response.content_type = 'application/json'
    response.headers['Access-Control-Allow-Origin']='*'    
    return response
