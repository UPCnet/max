# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented

from max.MADMax import MADMaxDB
from max.models import Activity
from max.decorators import MaxRequest, MaxResponse
from max.oauth2 import oauth2
from max.exceptions import MissingField

from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.rest.utils import searchParams
import re


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
    newactivity = Activity()
    newactivity.fromRequest(request, rest_params=rest_params)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newactivity.get('_id'):
        # Already Exists
        code = 200
    else:
        # New activity
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
    chash = request.params.get('context', None)
    if not chash:
        raise MissingField('You have to specify one context')

    mmdb = MADMaxDB(context.db)

    # subscribed contexts with read permission
    subscribed = [context.get('object', {}).get('url') for context in request.actor.subscribedTo.get('items', []) if 'read' in context.get('permissions', [])]

    # get the defined read context
    rcontext = mmdb.contexts.getItemsByhash(chash)[0]
    url = rcontext['object']['url']

    # regex query to find all contexts within url
    escaped = re.escape(url)
    url_regex = {'$regex': '^%s' % escaped}

    # search all contexts with public read permissions within url
    query = {'permissions.read': 'public', 'url': url_regex}
    public = [result.url for result in mmdb.contexts.search(query, show_fields=['url'])]

    query = {}                                                     # Search
    query.update({'verb': 'post'})                                 # 'post' activities
    query.update({'contexts.url': url_regex})                      # equal or child of url

    contexts_query = []
    if subscribed:
        subscribed_query = {'contexts.url': {'$in': subscribed}}  # that are subscribed contexts
        contexts_query.append(subscribed_query)                    # with read permission

    if public:                                                     # OR
        public_query = {'contexts.url': {'$in': public}}
        contexts_query.append(public_query)                        # pubic contexts

    if contexts_query:
        query.update({'$or': contexts_query})
        activities = mmdb.activity.search(query, sort="_id", flatten=1, **searchParams(request))
    else:
        # we have no public contexts and we are not subscribed to any context, so we
        # won't get anything
        activities = []

    # pass the read context as a extension to the resource
    handler = JSONResourceRoot(activities, extension=dict(context=rcontext.flatten()))
    return handler.buildResponse()


@view_config(route_name='activity', request_method='GET')
@MaxResponse
@MaxRequest
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
