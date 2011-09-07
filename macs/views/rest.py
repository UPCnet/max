from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk
import json
from bson import json_util

from macs.resources import Root
from macs.views.api import TemplateAPI

import time
from rfc3339 import rfc3339


@view_config(context=Root, request_method='POST', name="activity")
def addActivity(context, request):
    # import ipdb; ipdb.set_trace()
    try:
        checkRequestConsistency(request)
        data = extractPostData(request)
    except:
        return HTTPBadRequest()

    try:
        checkDataActivity(data)
    except:
        return HTTPBadRequest()

    # TODO: Do additional check about the content of the data (eg: 'author' is a valid system username)

    # Set published date format
    published = rfc3339(time.time())
    data['published'] = published

    # Insert activity in the database
    context.db.activity.insert(data)
    return HTTPOk()


@view_config(context=Root, request_method='GET', name="user_activity")
def getUserActivity(context, request):
    try:
        checkRequestConsistency(request)
    except:
        return HTTPBadRequest()

    if u'actor.id' in request.params:
        # The request is issued with query parameters
        data = {}
        data['actor.id'] = request.params.get(u'actor.id')
    else:
        # The request is issued by post
        data = extractPostData(request)

    # TODO: Do additional check about the content of the data (eg: 'author' is a valid system username)

    actor = {}
    actor['actor.id'] = data['actor.id']

    # (Change to the user_timeline method):
    # Search the database for the public TL of the user (or activity context) specified in JSON activitystrea.ms standard specs

    # Compile the results and forge the resultant collection object
    collection = {}
    activities = []
    cursor = context.db.activity.find(actor).limit(10)
    activities = [activity for activity in cursor]
    collection['totalItems'] = len(activities)
    collection['items'] = activities

    # Code the response with the encoder from BSON and return it with the appropiate content-type
    collection = json.dumps(collection, default=json_util.default)
    response = Response(collection)
    response.content_type = 'application/json'
    return response


@view_config(context=Root, request_method='POST', name="comment")
def addComment(context, request):
    # import ipdb; ipdb.set_trace()
    try:
        checkRequestConsistency(request)
        data = extractPostData(request)
    except:
        return HTTPBadRequest()

    try:
        checkDataComment(data)
    except:
        return HTTPBadRequest()

    # TODO: Do additional check about the content of the data (eg: 'author' is a valid system username)
    # and not comment in data

    # Set published date format
    published = rfc3339(time.time())
    data['published'] = published

    # Insert activity in the database
    context.db.activity.insert(data)
    return HTTPOk()    


def checkRequestConsistency(request):
    if request.content_type != 'application/json':
        raise

    # TODO: Do more consistency checks


def extractPostData(request):
    return json.loads(request.body)

    # TODO: Do more syntax and format checks of sent data


def checkDataActivity(data):
    if not 'actor' in data:
        raise
    # TODO: Check if data sent is consistent with JSON activitystrea.ms standard specs


def checkDataComment(data):
    if not 'actor' in data:
        raise
    # TODO: Check if data sent is consistent with JSON activitystrea.ms standard specs