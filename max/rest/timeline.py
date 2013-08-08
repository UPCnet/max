# -*- coding: utf-8 -*-
from pyramid.view import view_config

from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot
from max.decorators import MaxResponse, requirePersonActor
from max.oauth2 import oauth2
from max.rest.utils import searchParams
from max import LAST_AUTHORS_LIMIT, AUTHORS_SEARCH_MAX_QUERIES_LIMIT


def timelineQuery(mmdb, actor):
    # Add the activity of the requesting user
    actor_query = {'actor.username': actor['username']}

    # Add the activity of the people that the user follows
    actors_followings = []
    for following in actor['following']:
        actors_followings.append({'actor.username': following['username']})

    # Add the activity of the people that posts to a particular context
    contexts_followings = []
    for subscribed in actor['subscribedTo']:
        # Don't show conversations in timeline
            contexts_followings.append({'contexts.url': subscribed['url']})

    query_items = []
    query_items.append(actor_query)
    query_items += actors_followings
    query_items += contexts_followings

    query = {'$or': query_items}
    query['verb'] = 'post'
    # Include only visible activity, this includes activity with visible=True
    # and activity WITHOUT the visible field
    query['visible'] = {'$ne': False}
    return query


@view_config(route_name='timeline', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getUserTimeline(context, request):
    """
         /people/{username}/timeline

         Retorna totes les activitats d'un usuari
    """
    actor = request.actor
    mmdb = MADMaxDB(context.db)

    query = timelineQuery(mmdb, actor)

    sortBy_fields = {
        'activities': '_id',
        'comments': 'commented',
    }
    sort_order = sortBy_fields[request.params.get('sortBy', 'activities')]
    activities = mmdb.activity.search(query, sort=sort_order, flatten=1, keep_private_fields=False, **searchParams(request))

    handler = JSONResourceRoot(activities)
    return handler.buildResponse()


@view_config(route_name='timeline_authors', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getUserTimelineAuthors(context, request):
    """
         /people/{username}/timeline/authors

         Retorna totes els 8 ultims autors d'un timeline
    """
    # Get the author limit from the request or set a default
    author_limit = request.params.get('limit', LAST_AUTHORS_LIMIT)
    actor = request.actor
    mmdb = MADMaxDB(context.db)

    query = timelineQuery(mmdb, actor)

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
            queries += 1
            still_has_activities = len(activities) > 0
        if still_has_activities:
            activity = activities.pop(0)
            before = activity._id
            if activity.actor not in distinct_authors:
                distinct_authors.append(activity.actor)

    handler = JSONResourceRoot(distinct_authors)
    return handler.buildResponse()
