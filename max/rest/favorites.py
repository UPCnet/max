# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.MADMax import MADMaxDB
from max.exceptions import ObjectNotFound
from max.models import Activity
from max.rest.ResourceHandlers import JSONResourceEntity

from pyramid.httpexceptions import HTTPNotImplemented

from bson.objectid import ObjectId
from max.rest import endpoint


@endpoint(route_name='favorites', request_method='POST', requires_actor=True)
def favorite(context, request):
    """
    """
    activityid = request.matchdict['activity']

    mmdb = MADMaxDB(request.db)
    refering_activity = mmdb.activity[activityid]

    if refering_activity.has_favorite_from(request.actor):
        code = 200

        activities = MADMaxCollection(request.db.activity)
        query = {'verb': 'favorite', 'object._id': refering_activity['_id'], 'actor.username': request.actor.username}
        newactivity = activities.search(query)[-1]  # Pick the last one, so we get the last time user favorited this activiry

    else:
        code = 201
        # Prepare rest parameters to be merged with post data
        rest_params = {
            'verb': 'favorite',
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

        refering_activity.add_favorite_from(request.actor)

    newactivity['object']['favorites'] = refering_activity['favorites']  # Return the current favorites of the activity
    newactivity['object']['favoritesCount'] = refering_activity['favoritesCount']
    newactivity['object']['favorited'] = refering_activity.has_favorite_from(request.actor)
    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@endpoint(route_name='favorite', request_method='DELETE', requires_actor=True)
def unfavorite(context, request):
    """
    """
    activityid = request.matchdict['activity']

    mmdb = MADMaxDB(request.db)
    try:
        found_activity = mmdb.activity[activityid]
    except:
        raise ObjectNotFound("There's no activity with id: %s" % activityid)

    if not found_activity.has_favorite_from(request.actor):
        raise ObjectNotFound("You didn't previously favorited this activity: %s" % activityid)

    # Prepare rest parameters to be merged with post data
    rest_params = {
        'verb': 'unfavorite',
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

    found_activity.delete_favorite_from(request.actor)

    newactivity['object']['favorites'] = found_activity['favorites']
    newactivity['object']['favoritesCount'] = found_activity['favoritesCount']
    newactivity['object']['favorited'] = found_activity.has_favorite_from(request.actor)
    handler = JSONResourceEntity(newactivity.flatten(), status_code=200)
    return handler.buildResponse()


@endpoint(route_name='user_favorites', request_method='GET', requires_actor=True)
def getUserFavoritedActivities(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@endpoint(route_name='favorites', request_method='GET', requires_actor=True)
def getActivityFavorites(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover
