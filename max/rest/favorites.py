# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented

from max.decorators import MaxResponse, requirePersonActor
from max.oauth2 import oauth2
from max.MADMax import MADMaxDB, MADMaxCollection
from max.rest.ResourceHandlers import JSONResourceEntity
from max.models import Activity
from max.exceptions import ObjectNotFound

from bson.objectid import ObjectId


@view_config(route_name='user_favorites', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getUserFavoritedActivities(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='favorites', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getActivityFavorites(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='favorites', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def favorite(context, request):
    """
    """
    activityid = request.matchdict['activity']

    mmdb = MADMaxDB(context.db)
    refering_activity = mmdb.activity[activityid]

    if refering_activity.has_favorite_from(request.actor):
        code = 200

        activities = MADMaxCollection(context.db.activity)
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


@view_config(route_name='favorite', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def unfavorite(context, request):
    """
    """
    activityid = request.matchdict['activity']

    mmdb = MADMaxDB(context.db)
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
