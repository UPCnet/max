# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented

from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.decorators import MaxRequest, MaxResponse
from max.models import Activity
from max.oauth2 import oauth2
from max.rest.utils import flatten

from bson.objectid import ObjectId


@view_config(route_name='user_comments', request_method='GET')
@MaxResponse
@MaxRequest
def getUserComments(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='comments', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getActivityComments(context, request):
    """
    """
    activityid = request.matchdict['activity']

    mmdb = MADMaxDB(context.db)
    refering_activity = mmdb.activity[activityid]
    #cond1 = {'object.objectType' : 'comment'}
    #cond2 = {'object.inReplyTo._id' : refering_activity['_id']}
    #query = {'$and' : [ cond1, cond2 ] }
    #activities = mmdb.activity.search(query, sort="_id", limit=10, flatten=1)

    #handler = JSONResourceRoot(activities)
    replies = refering_activity.get('replies', {})
    items = replies.get('items', [])
    flatten(items)
    handler = JSONResourceRoot(items)
    return handler.buildResponse()


@view_config(route_name='comments', request_method='POST')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def addActivityComment(context, request):
    """
    POST /activities/{activity}/comments
    """
    #XXX TODO ara només es tracta la primera activitat,
    # s'ha de iterar si es vol que el comentari sigui de N activitats
    activityid = request.matchdict['activity']

    mmdb = MADMaxDB(context.db)
    refering_activity = mmdb.activity[activityid]

    # Prepare rest parameters to be merged with post data
    rest_params = {'verb': 'comment',
                   'object': {'inReplyTo': [{'_id':ObjectId(activityid),
                                             'objectType':refering_activity.object['objectType']}]}}

    # Initialize a Activity object from the request
    newactivity = Activity()
    newactivity.fromRequest(request, rest_params=rest_params)

    code = 201
    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    comment = dict(newactivity.object)
    comment['published'] = newactivity.published
    comment['author'] = request.actor
    comment['id'] = newactivity._id
    del comment['inReplyTo']

    refering_activity.addComment(comment)

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='comment', request_method='GET')
def getActivityComment(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='comments', request_method='PUT')
def modifyActivityComments(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='comments', request_method='DELETE')
def deleteActivityComments(context, request):
    """
    """
    return HTTPNotImplemented()
