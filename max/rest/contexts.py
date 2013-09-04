# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented
from pyramid.response import Response

from max import LAST_AUTHORS_LIMIT, AUTHORS_SEARCH_MAX_QUERIES_LIMIT
from max.MADMax import MADMaxDB
from max.exceptions import Unauthorized, ObjectNotFound
from max.oauth2 import oauth2
from max.decorators import MaxResponse, requirePersonActor
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
import os

from max.rest.utils import downloadTwitterUserImage, searchParams, flatten
import time


@view_config(route_name='public_contexts', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def getPublicContexts(context, request):
    """
        /contexts/public

        Return a list of public-subscribable contexts
    """
    mmdb = MADMaxDB(context.db)
    found_contexts = mmdb.contexts.search({'permissions.subscribe': 'public'}, **searchParams(request))

    handler = JSONResourceRoot(flatten(found_contexts, squash=['owner', 'creator', 'pubished']))
    return handler.buildResponse()


@view_config(route_name='context_activities_authors', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def getContextAuthors(context, request):
    """
        /contexts/{hash}/activities/authors
    """
    chash = request.matchdict['hash']
    mmdb = MADMaxDB(context.db)
    actor = request.actor
    author_limit = request.params.get('limit', LAST_AUTHORS_LIMIT)

    is_subscribed = chash in [subscription['hash'] for subscription in actor.subscribedTo]
    if not is_subscribed:
        raise Unauthorized("You're not allowed to access this context")

    query = {}
    query['contexts.hash'] = chash
    query['verb'] = 'post'
    # Include only visible activity, this includes activity with visible=True
    # and activity WITHOUT the visible field
    query['visible'] = {'$ne': False}

    sortBy_fields = {
        'activities': '_id',
        'comments': 'commented',
    }
    sort_order = sortBy_fields[request.params.get('sortBy', 'activities')]

    still_has_activities = True
    distinct_authors = []
    activities = []
    before = None
    queries = 0

    search_params = searchParams(request)
    while len(distinct_authors) < author_limit and still_has_activities and queries <= AUTHORS_SEARCH_MAX_QUERIES_LIMIT:
        if not activities:
            if before is not None:
                search_params['before'] = before
            activities = mmdb.activity.search(query, sort=sort_order, flatten=0, keep_private_fields=False, **search_params)
            still_has_activities = len(activities) > 0
        if still_has_activities:
            activity = activities.pop(0)
            before = activity._id
            if activity.actor not in distinct_authors:
                distinct_authors.append(activity.actor)

    handler = JSONResourceRoot(distinct_authors)
    return handler.buildResponse()


@view_config(route_name='context', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
def getContext(context, request):
    """
        /contexts/{hash}

        [RESTRICTED] Return a context by its hash.
    """
    mmdb = MADMaxDB(context.db)
    chash = request.matchdict.get('hash', None)
    found_context = mmdb.contexts.getItemsByhash(chash)

    if not found_context:
        raise ObjectNotFound("There's no context matching this url hash: %s" % chash)

    handler = JSONResourceEntity(found_context[0].flatten())
    return handler.buildResponse()


@view_config(route_name='context_avatar', request_method='GET')
@MaxResponse
def getContextAvatar(context, request):
    """
        /contexts/{hash}/avatar

        Return the context's avatar. To the date, this is only implemented to
        work integrated with Twitter.
    """
    chash = request.matchdict['hash']
    AVATAR_FOLDER = request.registry.settings.get('avatar_folder')
    context_image_filename = '%s/%s.png' % (AVATAR_FOLDER, chash)

    if not os.path.exists(context_image_filename):
        mmdb = MADMaxDB(context.db)
        found_context = mmdb.contexts.getItemsByhash(chash)
        if len(found_context) > 0:
            twitter_username = found_context[0]['twitterUsername']
            downloadTwitterUserImage(twitter_username, context_image_filename)
        else:
            raise ObjectNotFound("There's no context with hash %s" % chash)

    if os.path.exists(context_image_filename):
        # Calculate time since last download and set if we have to redownload or not
        modification_time = os.path.getmtime(context_image_filename)
        hours_since_last_modification = (time.time() - modification_time) / 60 / 60
        if hours_since_last_modification > 3:
            mmdb = MADMaxDB(context.db)
            found_context = mmdb.contexts.getItemsByhash(chash)
            twitter_username = found_context[0]['twitterUsername']
            downloadTwitterUserImage(twitter_username, context_image_filename)
    else:
        context_image_filename = '%s/missing.png' % (AVATAR_FOLDER)

    data = open(context_image_filename).read()
    image = Response(data, status_int=200)
    image.content_type = 'image/png'
    return image


@view_config(route_name='context', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
def DeleteContext(context, request):
    """
    """
    return HTTPNotImplemented  # pragma: no cover
