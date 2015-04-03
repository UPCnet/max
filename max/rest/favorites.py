# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.models import Activity
from max.rest import JSONResourceEntity
from max.rest import endpoint
from max.security.permissions import favorite
from max.security.permissions import unfavorite

from bson.objectid import ObjectId


@endpoint(route_name='favorites', request_method='POST', requires_actor=True, permission=favorite)
def favorite(activity, request):
    """
    """

    if activity.has_favorite_from(request.actor):
        code = 200

        activities = MADMaxCollection(request, 'activity')
        query = {'verb': 'favorite', 'object._id': activity['_id'], 'actor.username': request.actor.username}
        newactivity = activities.search(query)[-1]  # Pick the last one, so we get the last time user favorited this activiry

    else:
        code = 201
        # Prepare rest parameters to be merged with post data
        rest_params = {
            'verb': 'favorite',
            'object': {
                '_id': ObjectId(activity['_id']),
                'objectType': activity['objectType'],
            }
        }

        # Initialize a Activity object from the request
        newactivity = Activity.from_request(request, rest_params=rest_params)

        newactivity_oid = newactivity.insert()
        newactivity['_id'] = newactivity_oid

        activity.add_favorite_from(request.actor)

    newactivity['object']['favorites'] = activity['favorites']  # Return the current favorites of the activity
    newactivity['object']['favoritesCount'] = activity['favoritesCount']
    newactivity['object']['favorited'] = activity.has_favorite_from(request.actor)
    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@endpoint(route_name='favorite', request_method='DELETE', requires_actor=True, permission=unfavorite)
def unfavorite(activity, request):
    """
    """
    # Prepare rest parameters to be merged with post data
    rest_params = {
        'verb': 'unfavorite',
        'object': {
            '_id': ObjectId(activity['_id']),
            'objectType': activity['objectType'],
        }
    }

    # Initialize a Activity object from the request
    newactivity = Activity.from_request(request, rest_params=rest_params)

    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    activity.delete_favorite_from(request.actor)

    newactivity['object']['favorites'] = activity['favorites']
    newactivity['object']['favoritesCount'] = activity['favoritesCount']
    newactivity['object']['favorited'] = activity.has_favorite_from(request.actor)
    handler = JSONResourceEntity(newactivity.flatten(), status_code=200)
    return handler.buildResponse()
