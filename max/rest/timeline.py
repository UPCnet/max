# -*- coding: utf-8 -*-
from max import AUTHORS_SEARCH_MAX_QUERIES_LIMIT
from max import LAST_AUTHORS_LIMIT
from max.rest import JSONResourceRoot
from max.rest import endpoint
from max.rest.sorting import sorted_query
from max.security.permissions import list_activities


def timelineQuery(actor):
    # Add the activity of the requesting user
    actor_query = {'actor.username': actor['username']}

    # Add the activity of the people that the user follows
    actors_followings = []
    for following in actor.get('following', []):
        actors_followings.append({'actor.username': following['username']})

    # Add the activity of the people that posts to a particular context
    contexts_followings = []
    for subscribed in actor.get('subscribedTo', []):
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


@endpoint(route_name='timeline', request_method='GET', permission=list_activities)
def getUserTimeline(user, request):
    """
        Get user timeline
    """
    query = timelineQuery(user)

    activities = sorted_query(request, request.db.activity, query, flatten=1)

    handler = JSONResourceRoot(request, activities)
    return handler.buildResponse()


@endpoint(route_name='timeline_authors', request_method='GET', permission=list_activities)
def getUserTimelineAuthors(user, request):
    """
        Get timeline authors
    """
    # Get the author limit from the request or set a default
    author_limit = int(request.params.get('limit', LAST_AUTHORS_LIMIT))
    query = timelineQuery(user)

    # Save full author object to construct the response
    # and a separate username field to make the unique-fication easier

    distinct_authors = []
    distinct_usernames = []

    feed_parameters = {
        'queries': 0,
        'before': None
    }

    def extra_params():
        params = {'limit': 30}
        if feed_parameters['before'] is not None:
            params['before'] = feed_parameters['before']
        return params

    def feed_activities():
        """
            Keep feeding a continuous flow of activitesm making as many queries
            as needed, while not reaching defined limit
        """
        while feed_parameters['queries'] <= AUTHORS_SEARCH_MAX_QUERIES_LIMIT:
            activities = sorted_query(request, request.db.activity, query, count=False, **extra_params())
            activity = None
            for activity in activities:
                yield activity

            # Once exhausted the first query, prepare for the next round
            if activity:
                feed_parameters['before'] = activity['_id']
                feed_parameters['queries'] += 1
            else:
                raise StopIteration

    # While there are activities coming from queries, collect distinct usernames until
    # target author_limit found

    for activity in feed_activities():
        if activity['actor']['username'] not in distinct_usernames:
            distinct_authors.append(activity['actor'])
            distinct_usernames.append(activity['actor']['username'])

        if len(distinct_usernames) == author_limit:
            break

    is_head = request.method == 'HEAD'
    data = len(distinct_usernames) if is_head else distinct_authors

    handler = JSONResourceRoot(request, data, stats=is_head)
    return handler.buildResponse()
