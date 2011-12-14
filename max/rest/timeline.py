from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk

import json
from bson import json_util
from pymongo.objectid import ObjectId

from max.resources import Root
from max.rest.utils import checkDataAddUser, checkRequestConsistency, extractPostData

from max.MADMax import MADMaxDB

import datetime


@view_config(route_name='timeline', request_method='GET')
def TimelineResourceRoot(context, request):
    """
         /users/{displayName}/timeline

         Retorna totes les activitats d'un usuari
    """
    displayName = request.matchdict['user_displayName']

    mmdb = MADMaxDB(context.db)

    actor = mmdb.users.getItemsBydisplayName(displayName)[0]

    query = {'actor._id': actor['_id']}
    activities = [a for a in mmdb.activity.collection.find(query) ]
    
    json_data = json.dumps(activities, default=json_util.default)
    response = Response(json_data)
    response.content_type = 'application/json'
    response.headers['Access-Control-Allow-Origin']='*'   
    return response 


