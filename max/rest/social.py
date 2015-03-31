# -*- coding: utf-8 -*-
from max.rest.ResourceHandlers import JSONResourceEntity


from pyramid.httpexceptions import HTTPNoContent
from max.rest import endpoint

from max.MADMax import MADMaxCollection
from max.models import Activity
from max.security.permissions import like, unlike, flag, unflag
from pyramid.httpexceptions import HTTPNotImplemented

from bson.objectid import ObjectId


@endpoint(route_name='likes', request_method='POST', requires_actor=True, permission=like)
def like(activity, request):
    """
    """
    if activity.has_like_from(request.actor):
        code = 200

        activities = MADMaxCollection(request.db.activity)
        query = {'verb': 'like', 'object._id': activity['_id'], 'actor.username': request.actor.username}
        newactivity = activities.search(query)[-1]  # Pick the last one, so we get the last time user liked this activity

    else:
        code = 201
        # Prepare rest parameters to be merged with post data
        rest_params = {
            'verb': 'like',
            'object': {
                '_id': ObjectId(activity['_id']),
                'objectType': activity['objectType'],
            }
        }

        # Initialize a Activity object from the request
        newactivity = Activity()
        newactivity.fromRequest(request, rest_params=rest_params)

        newactivity_oid = newactivity.insert()
        newactivity['_id'] = newactivity_oid

        activity.add_like_from(request.actor)

    newactivity['object']['likes'] = activity['likes']  # Return the current likes of the activity
    newactivity['object']['likesCount'] = activity['likesCount']  # Return the current likes of the activity
    newactivity['object']['liked'] = activity.has_like_from(request.actor)
    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@endpoint(route_name='like', request_method='DELETE', requires_actor=True, permission=unlike)
def unlike(activity, request):
    """
    """

    # Prepare rest parameters to be merged with post data
    rest_params = {
        'verb': 'unlike',
        'object': {
            '_id': ObjectId(activity['_id']),
            'objectType': activity['objectType'],
        }
    }

    # Initialize a Activity object from the request
    newactivity = Activity()
    newactivity.fromRequest(request, rest_params=rest_params)

    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    activity.delete_like_from(request.actor)

    newactivity['object']['likes'] = activity['likes']
    newactivity['object']['likesCount'] = activity['likesCount']
    newactivity['object']['liked'] = activity.has_like_from(request.actor)
    handler = JSONResourceEntity(newactivity.flatten(), status_code=200)
    return handler.buildResponse()


@endpoint(route_name='flag', request_method='POST', requires_actor=True, permission=flag)
def flagActivity(activity, request):
    """
         Sets the flagged mark on an activity
    """
    status_code = 200

    # Flag only if not already flagged
    if activity.get('flagged', None) is None:
        activity.flag()
        activity.save()
        status_code = 201

    handler = JSONResourceEntity(activity.flatten(), status_code=status_code)
    return handler.buildResponse()


@endpoint(route_name='flag', request_method='DELETE', requires_actor=True, permission=unflag)
def unflagActivity(activity, request):
    """
         Unsets the flagged mark on an activity
    """
    activity.unflag()
    activity.save()

    return HTTPNoContent()


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
