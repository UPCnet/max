# -*- coding: utf-8 -*-
from max.MADMax import MADMaxDB
from max.exceptions import Forbidden
from max.exceptions import ObjectNotFound
from max.exceptions import Unauthorized
from max.rest.ResourceHandlers import JSONResourceEntity


from pyramid.httpexceptions import HTTPNoContent
from max.rest import endpoint
from max.security.permissions import flag_activity, unflag_activity

from max.MADMax import MADMaxCollection
from max.models import Activity

from pyramid.httpexceptions import HTTPNotImplemented

from bson.objectid import ObjectId


@endpoint(route_name='user_likes', request_method='GET', requires_actor=True)
def getUserLikedActivities(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@endpoint(route_name='likes', request_method='GET', requires_actor=True)
def getActivityLikes(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@endpoint(route_name='likes', request_method='POST', requires_actor=True)
def like(context, request):
    """
    """
    activityid = request.matchdict['activity']

    mmdb = MADMaxDB(request.db)
    refering_activity = mmdb.activity[activityid]

    if refering_activity.has_like_from(request.actor):
        code = 200

        activities = MADMaxCollection(request.db.activity)
        query = {'verb': 'like', 'object._id': refering_activity['_id'], 'actor.username': request.actor.username}
        newactivity = activities.search(query)[-1]  # Pick the last one, so we get the last time user liked this activiry

    else:
        code = 201
        # Prepare rest parameters to be merged with post data
        rest_params = {
            'verb': 'like',
            'object': {
                '_id': ObjectId(activityid),
                'objectType': refering_activity['objectType'],
            }
        }

        # Initialize a Activity object from the request
        newactivity = Activity()
        newactivity.fromRequest(request, rest_params=rest_params)

        newactivity_oid = newactivity.insert()
        newactivity['_id'] = newactivity_oid

        refering_activity.add_like_from(request.actor)
    newactivity['object']['likes'] = refering_activity['likes']  # Return the current likes of the activity
    newactivity['object']['likesCount'] = refering_activity['likesCount']  # Return the current likes of the activity
    newactivity['object']['liked'] = refering_activity.has_like_from(request.actor)
    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@endpoint(route_name='like', request_method='DELETE', requires_actor=True)
def unlike(context, request):
    """
    """
    activityid = request.matchdict['activity']

    mmdb = MADMaxDB(request.db)
    try:
        found_activity = mmdb.activity[activityid]
    except:
        raise ObjectNotFound("There's no activity with id: %s" % activityid)

    if not found_activity.has_like_from(request.actor):
        raise ObjectNotFound("You didn't previously liked this activity: %s" % activityid)

    # Prepare rest parameters to be merged with post data
    rest_params = {
        'verb': 'unlike',
        'object': {
            '_id': ObjectId(activityid),
            'objectType': found_activity['objectType'],
        }
    }

    # Initialize a Activity object from the request
    newactivity = Activity()
    newactivity.fromRequest(request, rest_params=rest_params)

    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    found_activity.delete_like_from(request.actor)

    newactivity['object']['likes'] = found_activity['likes']
    newactivity['object']['likesCount'] = found_activity['likesCount']
    newactivity['object']['liked'] = found_activity.has_like_from(request.actor)
    handler = JSONResourceEntity(newactivity.flatten(), status_code=200)
    return handler.buildResponse()


@endpoint(route_name='flag', request_method='POST', requires_actor=True, permission=flag_activity)
def flagActivity(context, request):
    """
         Sets the flagged mark on an activity
    """
    mmdb = MADMaxDB(request.db)
    activityid = request.matchdict.get('activity', None)
    try:
        found_activity = mmdb.activity[activityid]
    except:
        raise ObjectNotFound("There's no activity with id: %s" % activityid)

    status_code = 200
    # Check if the activity is flaggable by the actor
    if found_activity.get('contexts', []):
        ctxt = found_activity.contexts[0]
        subscription = request.actor.getSubscription(ctxt)
        if 'flag' not in subscription['permissions']:
            raise Unauthorized("You are not allowed to flag this activity.")

        # Flag only if not already flagged
        if found_activity.get('flagged', None) is None:
            found_activity.flag()
            found_activity.save()
            status_code = 201

    else:
        raise Forbidden("Only context activities can be flagged.")

    handler = JSONResourceEntity(found_activity.flatten(), status_code=status_code)
    return handler.buildResponse()


@endpoint(route_name='flag', request_method='DELETE', requires_actor=True, permission=unflag_activity)
def unflagActivity(context, request):
    """
         Unsets the flagged mark on an activity
    """
    mmdb = MADMaxDB(request.db)
    activityid = request.matchdict.get('activity', None)
    try:
        found_activity = mmdb.activity[activityid]
    except:
        raise ObjectNotFound("There's no activity with id: %s" % activityid)

    # Check if the activity is flaggable by the actor
    if found_activity.get('contexts', []):
        ctxt = found_activity.contexts[0]
        subscription = request.actor.getSubscription(ctxt)
        if 'flag' not in subscription['permissions']:
            raise Unauthorized("You are not allowed to unflag this activity.")
    else:
        raise Forbidden("Only context activities can be unflagged.")

    found_activity.unflag()
    found_activity.save()

    return HTTPNoContent()
