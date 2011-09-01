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
    if request.content_type != 'application/json':
        return HTTPBadRequest()

    # TODO: Do more consistency, syntax and format checks of sent data
    try:
        data = json.loads(request.body)
    except:
        return HTTPBadRequest()

    # TODO: Do additional check about the content of the data (eg: 'author' is a valid system username)

    # TODO: Check if data sent is consistent and consistent with JSON activitystrea.ms standard specs

    # Set published
    published = rfc3339(time.time())
    data['published'] = published

    # Insert activity in the database
    context.db.activity.insert(data)
    return HTTPOk()


@view_config(context=Root, request_method='GET', name="activity")
def getActivity(context, request):
    # import ipdb; ipdb.set_trace( )
    if request.content_type != 'application/json':
        return HTTPBadRequest()
    # TODO: Do more consistency, syntax and format checks of sent data
    if request.params.has_key(u'actor.id'):
        data = {}
        data['actor.id'] = request.params.get(u'actor.id')
    else:
        try:
            data = json.loads(request.body)
        except:
            return HTTPBadRequest()

    # TODO: Do additional check about the content of the data (eg: 'author' is a valid system username)
    actor = {}
    actor['actor.id'] = data['actor.id']

    # Search the database for the public TL of the user (or activity context) specified in JSON activitystrea.ms standard specs

    # Compile the results and forge the resultant collection object
    collection = {}
    activities = []
    cursor = context.db.activity.find(actor).limit(10)
    activities = [activity for activity in cursor]
    # collection['totalItems'] = len(activities)
    collection['items'] = activities

    # Code the response with the encoder from BSON and return it with the appropiate content-type
    collection = json.dumps(collection, default=json_util.default)
    response = Response(collection)
    response.content_type = 'application/json'
    return response
