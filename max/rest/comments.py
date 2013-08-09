# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented, HTTPNoContent

from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.decorators import MaxResponse, requirePersonActor
from max.exceptions import ObjectNotFound, Unauthorized
from max.models import Activity
from max.oauth2 import oauth2
from max.rest.utils import flatten

from bson.objectid import ObjectId


@view_config(route_name='user_comments', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
def getUserComments(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='activity_comments', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getActivityComments(context, request):
    """
        /activities/{activity}/comments

        Return the comments for an activity.
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
    items = replies
    result = flatten(items, keep_private_fields=False)
    handler = JSONResourceRoot(result)
    return handler.buildResponse()


@view_config(route_name='activity_comments', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def addActivityComment(context, request):
    """
        /activities/{activity}/comments

        Post a comment to an activity.
    """
    #XXX TODO ara només es tracta la primera activitat,
    # s'ha de iterar si es vol que el comentari sigui de N activitats
    activityid = request.matchdict['activity']

    mmdb = MADMaxDB(context.db)
    refering_activity = mmdb.activity[activityid]

    # Prepare rest parameters to be merged with post data
    rest_params = {
        'verb': 'comment',
        'object': {
            'inReplyTo': [{
                '_id': ObjectId(activityid),
                'objectType': refering_activity.object['objectType']
            }]
        }
    }

    # Initialize a Activity object from the request
    newactivity = Activity()
    newactivity.fromRequest(request, rest_params=rest_params)

    code = 201
    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    comment = dict(newactivity.object)
    comment['published'] = newactivity.published
    comment['actor'] = request.actor
    comment['id'] = newactivity._id
    del comment['inReplyTo']
    refering_activity.addComment(comment)

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='activity_comment', request_method='GET')
def getActivityComment(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='activity_comments', request_method='PUT')
def modifyActivityComments(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='activity_comment', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def deleteActivityComment(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    activityid = request.matchdict.get('activity', None)
    commentid = request.matchdict.get('comment', None)
    try:
        found_activity = mmdb.activity[activityid]
    except:
        raise ObjectNotFound("There's no activity with id: %s" % activityid)

    comment = found_activity.get_comment(commentid)
    if not comment:
        raise ObjectNotFound("There's no comment with id: %s" % commentid)

    if found_activity.deletable or request.actor.username == comment['actor']['username']:
        found_activity.delete_comment(commentid)
    else:
        raise Unauthorized("You're not allowed to delete this comment")

    return HTTPNoContent()


@view_config(route_name='comments', request_method='DELETE')
def deleteActivityComments(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover
