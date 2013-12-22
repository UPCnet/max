# -*- coding: utf-8 -*-
from pyramid.view import view_config

from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot
from max.decorators import MaxResponse, requirePersonActor
from max.oauth2 import oauth2
from max.rest.utils import searchParams
from max import LAST_AUTHORS_LIMIT, AUTHORS_SEARCH_MAX_QUERIES_LIMIT


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

    sortBy_fields = {
        'activities': '_id',
        'comments': 'lastComment',
        'likes': 'likesCount'
    }
    sort_type = request.params.get('sortBy', 'activities')
    sort_order = sortBy_fields[sort_type]

    search_params = searchParams(request)
    # If we're in a 2+ page of likes
    if sort_type == 'likes' and 'before' in search_params and 'limit' in search_params:
        # Get the likes Count of the last object of the previous page
        last_page_object = mmdb.activity.search({'_id': search_params['before']})
        likes_count = last_page_object[0].likesCount
        # Target query to search items including the ones with the same likesCount than the last object
        # Widen the limit of resuts to the double as we may get duplicated results that we'll have to filter out later
        # the item referenced in before param will be included in the results of this search
        search_params['offset'] = likes_count + 1
        original_limit = int(search_params['limit'])
        search_params['limit'] = search_params['limit'] * 2

    activities = mmdb.activity.search(query, sort=sort_order, flatten=1, squash=['favorites', 'likes'], keep_private_fields=False, **search_params)

    # If we're in a 2+ page of likes, continue filtering
    if sort_type == 'likes' and 'before' in search_params and 'limit' in search_params:
        start = 0
        for pos, activity in enumerate(activities):
            if activity['id'] == str(search_params['before']):
                # We found the object referenced in before param, so we pick the next item as the first
                start = pos + 1
                break
        # Pick activities according to the original limit, excluding the ones included in the latest page
        activities = activities[start:start + original_limit]

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

    sortBy_fields = {
        'activities': '_id',
        'comments': 'lastComment',
    }
    sort_order = sortBy_fields[request.params.get('sortBy', 'activities')]

    still_has_activities = True

    # Save full author object to construct de response
    # and a separate username field to make the uniquefication easier
    distinct_authors = []
    distinct_usernames = []

    activities = []
    before = None
    queries = 0

    search_params = searchParams(request)
    while len(distinct_usernames) < author_limit and still_has_activities and queries <= AUTHORS_SEARCH_MAX_QUERIES_LIMIT:
        if not activities:
            if before is not None:
                search_params['before'] = before
            activities = mmdb.activity.search(query, sort=sort_order, flatten=0, keep_private_fields=False, **search_params)
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
