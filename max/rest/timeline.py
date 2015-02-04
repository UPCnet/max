# -*- coding: utf-8 -*-
from max import AUTHORS_SEARCH_MAX_QUERIES_LIMIT
from max import LAST_AUTHORS_LIMIT
from max.MADMax import MADMaxDB
from max.decorators import MaxResponse
from max.decorators import requirePersonActor
from max.oauth2 import oauth2
from max.rest.ResourceHandlers import JSONResourceRoot
from max.rest.utils import searchParams
from max.rest.sorting import sorted_query

from pyramid.view import view_config


def timelineQuery(actor):
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

    query = timelineQuery(actor)

    activities = sorted_query(request, mmdb.activity, query, flatten=1)

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
    author_limit = int(request.params.get('limit', LAST_AUTHORS_LIMIT))
    actor = request.actor
    mmdb = MADMaxDB(context.db)

    query = timelineQuery(actor)

    still_has_activities = True

    # Save full author object to construct de response
    # and a separate username field to make the uniquefication easier
    distinct_authors = []
    distinct_usernames = []

    activities = []
    before = None
    queries = 0

    while len(distinct_usernames) < author_limit and still_has_activities and queries <= AUTHORS_SEARCH_MAX_QUERIES_LIMIT:
        if not activities:
            extra = {'before': before} if before else {}
            activities = sorted_query(request, mmdb.activity, query, **extra)
            queries += 1
            still_has_activities = len(activities) > 0
        if still_has_activities:
            activity = activities.pop(0)
            before = activity._id
            if activity.actor['username'] not in distinct_usernames:
                distinct_authors.append(activity.actor)
                distinct_usernames.append(activity.actor['username'])

    handler = JSONResourceRoot(distinct_authors)
    return handler.buildResponse()
