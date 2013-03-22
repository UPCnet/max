# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent

from max.models import Activity
from max.oauth2 import oauth2, restricted
from max.decorators import MaxResponse, requirePersonActor, requireContextActor
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceEntity
from max.rest.ResourceHandlers import JSONResourceRoot
from max.exceptions import ObjectNotFound


@view_config(route_name='admin_user_activities', request_method='POST')
@MaxResponse
@requirePersonActor(force_own=False)
@oauth2(['widgetcli'])
@restricted(['Manager'])
def addAdminUserActivity(context, request):
    """
         /admin/people|contexts/{username|hash}/activities

         Add activity impersonated as a valid MAX user or context
    """
    rest_params = {'actor': request.actor,
                   'verb': 'post'}

    # Initialize a Activity object from the request
    newactivity = Activity(request)
    newactivity.fromRequest(request, rest_params=rest_params)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newactivity.get('_id'):
        # Already Exists
        code = 200
    else:
        # New User
        code = 201
        activity_oid = newactivity.insert()
        newactivity['_id'] = activity_oid

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='admin_context_activities', request_method='POST')
@MaxResponse
@requireContextActor
@oauth2(['widgetcli'])
@restricted(['Manager'])
def addAdminContextActivity(context, request):
    """
         /admin/people|contexts/{username|hash}/activities

         Add activity impersonated as a valid MAX user or context
    """
    rest_params = {'actor': request.actor,
                   'verb': 'post'}

    # Initialize a Activity object from the request
    newactivity = Activity(request)
    newactivity.fromRequest(request, rest_params=rest_params)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newactivity.get('_id'):
        # Already Exists
        code = 200
    else:
        # New User
        code = 201
        activity_oid = newactivity.insert()
        newactivity['_id'] = activity_oid

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='admin_activities', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@restricted(['Manager'])
def getActivities(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    activities = mmdb.activity.dump(flatten=1)
    handler = JSONResourceRoot(activities)
    return handler.buildResponse()


@view_config(route_name='admin_activity', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
@restricted(['Manager'])
def deleteActivity(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    activityid = request.matchdict.get('id', None)
    try:
        found_activity = mmdb.activity[activityid]
    except:
        raise ObjectNotFound("There's no activity with id: %s" % activityid)

    found_activity.delete()
    return HTTPNoContent()
