from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk

import json
from bson import json_util
from pymongo.objectid import ObjectId
from pymongo import DESCENDING

from macs.resources import Root
from macs.rest.utils import checkQuery, checkIsValidQueryUser, checkRequestConsistency, extractPostData

import time
from rfc3339 import rfc3339
from copy import deepcopy


@view_config(context=Root, request_method='GET', name="user_activity")
def getUserActivity(context, request):
    try:
        checkRequestConsistency(request)
    except:
        return HTTPBadRequest()

    if request.params:
        # The request is issued with query parameters
        data = request.params
    else:
        # The request is issued by POST
        data = extractPostData(request)

    try:
        checkQuery(data)
        checkIsValidQueryUser(context, data)
    except:
        return HTTPBadRequest()

    # Once verified the id of the user, search for the id of the user given its displayName
    # We suppose that the displayName is unique
    user = context.db.users.find_one({'displayName': data['displayName']}, {'_id': 1, 'following': 1, 'subscribedTo': 1})

    # The query has to have this syntax {'$or': [{'actor.displayName': 'victor'}, {'actor.displayName': 'javier'}] }
    query = {'$or': []}
    query['$or'].append({'actor._id': user['_id']})

    # Add the activity of the people that the user follows
    for following in user['following']['items']:
        query['$or'].append({'actor._id': following['_id']})

    for subscribed in user['subscribedTo']['items']:
        query['$or'].append({'target.url': subscribed['url']})

    # (Change to the user_timeline method):
    # Search the database for the public TL of the user (or activity context) specified in JSON activitystrea.ms standard specs

    # Compile the results and forge the resultant collection object
    collection = {}
    activities = []
    cursor = context.db.activity.find(query).sort("_id", DESCENDING).limit(10)
    activities = [activity for activity in cursor]
    collection['totalItems'] = len(activities)
    collection['items'] = activities
    # Code the response with the encoder from BSON and return it with the appropiate content-type
    collection = json.dumps(collection, default=json_util.default)
    response = Response(collection)
    response.content_type = 'application/json'
    return response


@view_config(context=Root, request_method='GET', name="user_activity_by_scope")
def getUserActivityByScope(context, request):
    try:
        checkRequestConsistency(request)
    except:
        return HTTPBadRequest()

    if request.params:
        # The request is issued with query parameters
        data = request.params
    else:
        # The request is issued by POST
        data = extractPostData(request)

    try:
        checkQuery(data)
        checkIsValidQueryUser(context, data)
        # Verify that the scopes are valid URLs
    except:
        return HTTPBadRequest()

    # Once verified the id of the user, search for the id of the user given its displayName
    # We suppose that the displayName is unique
    user = context.db.users.find_one({'displayName': data['displayName']}, {'_id': 1})

    # The query has to have this syntax {'$or': [{'actor.displayName': 'victor'}, {'actor.displayName': 'javier'}] }
    query = {'$or': []}
    query['actor._id'] = user['_id']

    # Add the activity of the people that the user follows
    for scope in data['scopes']:
        query['$or'].append({'target.url': scope})

    # (Change to the user_timeline method):
    # Search the database for the public TL of the user (or activity context) specified in JSON activitystrea.ms standard specs

    # Compile the results and forge the resultant collection object
    collection = {}
    activities = []
    cursor = context.db.activity.find(query).sort("_id", DESCENDING).limit(10)
    activities = [activity for activity in cursor]
    collection['totalItems'] = len(activities)
    collection['items'] = activities
    # Code the response with the encoder from BSON and return it with the appropiate content-type
    collection = json.dumps(collection, default=json_util.default)
    response = Response(collection)
    response.content_type = 'application/json'
    return response
