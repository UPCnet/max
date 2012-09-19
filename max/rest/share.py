# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk, HTTPNotImplemented

import json
from bson import json_util
from bson.objectid import ObjectId

from max.resources import Root
from max.rest.utils import checkIsValidActivity, checkDataShare, checkIsValidUser, checkRequestConsistency, extractPostData

import time
from rfc3339 import rfc3339
from copy import deepcopy


@view_config(route_name='user_shares', request_method='GET')
def getUserSharedActivities(context, request):
    """
    """
    return HTTPNotImplemented()

@view_config(route_name='shares', request_method='GET')
def getActivityShares(context, request):
    """
    """
    return HTTPNotImplemented()

@view_config(route_name='share', request_method='GET')
def getActivityShare(context, request):
    """
    """
    return HTTPNotImplemented()

@view_config(route_name='shares', request_method='POST')
def share(context, request):
    """
    """
    return HTTPNotImplemented()

@view_config(route_name='share', request_method='DELETE')
def unshare(context, request):
    """
    """
    return HTTPNotImplemented()




# @view_config(context=Root, request_method='POST', name="share")
# def Share(context, request):
#     # import ipdb; ipdb.set_trace()
#     try:
#         checkRequestConsistency(request)
#         data = extractPostData(request)
#     except:
#         return HTTPBadRequest()

#     try:
#         checkDataShare(data)
#         checkIsValidUser(context, data)
#         checkIsValidActivity(context, data)
#     except:
#         return HTTPBadRequest()

#     # Once verified the id of the user, convert the userid to an ObjectId
#     data['actor']['_id'] = ObjectId(data['actor']['id'])
#     del data['actor']['id']

#     # Once verified the activity is valid, get the activity object
#     activity = context.db.activity.find_one({'_id': ObjectId(data['object']['id'])})
#     del data['object']['id']

#     # Insert it in the data object field and set appropiate values
#     data['object'] = activity
#     data['object']['objectType'] = 'activity'

#     # Set published date format
#     published = rfc3339(time.time())
#     data['published'] = published

#     # Insert activity in the database
#     context.db.activity.insert(data)

#     return HTTPOk()
