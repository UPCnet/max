from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk, HTTPNotImplemented

import json
from bson import json_util
from pymongo.objectid import ObjectId
from max.resources import Root
from max.rest.utils import checkDataunFollowContext, checkDataFollowContext, checkIsValidUser, checkAreValidFollowUsers, checkDataFollow, checkDataunFollow, checkRequestConsistency, extractPostData

import time
from rfc3339 import rfc3339
from copy import deepcopy


@view_config(route_name='subscriptions', request_method='GET')
def getUserSubscriptions(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='subscription', request_method='GET')
def getUserSubscription(context, request):
    """
    """
    return HTTPNotImplemented()

@view_config(route_name='subscription', request_method='POST')
def subscribe(context, request):
    """
    """
    return HTTPNotImplemented()

@view_config(route_name='subscription', request_method='DELETE')
def unsubscribe(context, request):
    """
    """
    return HTTPNotImplemented()


###################### Per comprovar els follows/unfollows al afegir, cal comprovar que no el segueixi previament


# @view_config(context=Root, request_method='POST', name="follow_context")
# def followContext(context, request):
#     # import ipdb; ipdb.set_trace()
#     try:
#         checkRequestConsistency(request)
#         data = extractPostData(request)
#     except:
#         return HTTPBadRequest()

#     try:
#         checkDataFollowContext(data)
#         checkIsValidUser(context, data)
#     except:
#         return HTTPBadRequest()

#     # Check if already follows

#     # Once verified the id of the users, convert their userid to an ObjectId
#     data['actor']['_id'] = ObjectId(data['actor']['id'])
#     del data['actor']['id']

#     # Set published date format
#     published = rfc3339(time.time())
#     data['published'] = published

#     # Insert activity in the database
#     context.db.activity.insert(data)

#     context.db.users.update({'_id': data['actor']['_id']},
#                             {'$push': {'subscribedTo.items': {'url': data['object']['url']}},
#                             '$inc': {'subscribedTo.totalItems': 1}})

#     return HTTPOk()


# @view_config(context=Root, request_method='POST', name="unfollow_context")
# def unFollowContext(context, request):
#     # import ipdb; ipdb.set_trace()
#     try:
#         checkRequestConsistency(request)
#         data = extractPostData(request)
#     except:
#         return HTTPBadRequest()

#     try:
#         checkDataunFollowContext(data)
#         checkIsValidUser(context, data)
#     except:
#         return HTTPBadRequest()

#     # Check if already not follows

#     # Once verified the id of the users, convert their userid to an ObjectId
#     data['actor']['_id'] = ObjectId(data['actor']['id'])
#     del data['actor']['id']

#     # Set published date format
#     published = rfc3339(time.time())
#     data['published'] = published

#     # Insert activity in the database
#     context.db.activity.insert(data)

#     context.db.users.update({'_id': data['actor']['_id']},
#                             {'$pull': {'subscribedTo.items': {'url': data['object']['url']}},
#                             '$inc': {'subscribedTo.totalItems': -1}})

#     return HTTPOk()
