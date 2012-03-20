from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented

from max.MADMax import MADMaxDB
from max.models import Activity
from max.decorators import MaxRequest, MaxResponse
from max.oauth2 import oauth2
from max.exceptions import MissingField, Unauthorized

from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.rest.utils import searchParams, hasPermissionInContexts


@view_config(route_name='user_activities', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getUserActivities(context, request):
    """
         /people/{username}/activities

         Retorna all activities generated by a user
    """

    mmdb = MADMaxDB(context.db)
    query = {'actor._id': request.actor['_id']}
    activities = mmdb.activity.search(query, sort="_id", flatten=1)

    handler = JSONResourceRoot(activities)
    return handler.buildResponse()


@view_config(route_name='user_activities', request_method='POST')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def addUserActivity(context, request):
    """
         /users/{username}/activities

         Afegeix una activitat
    """
    rest_params = {'actor': request.actor,
                   'verb': 'post'}

    # Initialize a Activity object from the request
    newactivity = Activity(request, rest_params=rest_params)

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


@view_config(route_name='activities', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getActivities(context, request):
    """
         /activities

         Retorna all activities, optionaly filtered by context
    """
    urls = request.params.getall('contexts')
    if urls == []:
        raise MissingField, 'You have to specify at least one context'

    hasPermissionInContexts(request.actor, 'read', urls)
    # If we reached here, we have permission to search for all urls in urls

    # Add all the activities posted on particular contexts
    contexts_followings_query = []
    for url in urls:
        contexts_followings_query.append({'contexts.url': url})

    query = {'verb': 'post'}
    if contexts_followings_query:
        query = {'$or': contexts_followings_query}

    mmdb = MADMaxDB(context.db)
    activities = mmdb.activity.search(query, sort="_id", flatten=1, **searchParams(request))
    handler = JSONResourceRoot(activities)
    return handler.buildResponse()


@view_config(route_name='activity', request_method='GET')
#@MaxResponse
#@MaxRequest
def getActivity(context, request):
    """
         /activities/{activity}

         Mostra una activitat
    """

    mmdb = MADMaxDB(context.db)
    activity_oid = request.matchdict['activity']
    activity = mmdb.activity[activity_oid].flatten()

    handler = JSONResourceEntity(activity)
    return handler.buildResponse()


@view_config(route_name='activity', request_method='DELETE')
def deleteActivity(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='activity', request_method='PUT')
def modifyActivity(context, request):
    """
    """
    return HTTPNotImplemented()
