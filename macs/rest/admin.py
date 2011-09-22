from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk

import json
from bson import json_util
from pymongo.objectid import ObjectId

from macs.resources import Root
from macs.rest.utils import checkDataAddUser, checkRequestConsistency, extractPostData

import datetime


@view_config(context=Root, request_method='POST', name="add_user")
def addUser(context, request):
    try:
        checkRequestConsistency(request)
        data = extractPostData(request)
    except:
        return HTTPBadRequest()

    try:
        checkDataAddUser(data)
    except:
        return HTTPBadRequest()

    result = context.db.users.find_one({'displayName': data['displayName']}, {'_id': 1})

    if not result:
        # Create the new user
        newuser = {'displayName': data['displayName'],
                   'last_login': datetime.datetime.now(),
                   'following': {'items': [], },
                   'subscribedTo': {'items': [], }
                   }
        # Insert user in the database
        userid = context.db.users.insert(newuser)
    else:
        # Return the id of the already existing user
        userid = result['_id']

    userid = json.dumps(userid, default=json_util.default)
    response = Response(userid)
    response.content_type = 'application/json'
    return response
