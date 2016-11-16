# -*- coding: utf-8 -*-
from max import AUTHORS_SEARCH_MAX_QUERIES_LIMIT
from max import LAST_AUTHORS_LIMIT
from max.rest import JSONResourceRoot
from max.rest import endpoint
from max.rest.sorting import sorted_query
from max.security.permissions import view_timeline


def timelineQuery(actor):
    """
        Construct the query used to get a user's timeline
    """
    # As this query may be composed by several $or clauses, we define which
    # query fields are common to all clauses
    # This includes only visible activity (this is: activity with visible=True AND
    # activity WITHOUT the visible field ) and activities with verb 'post'
    common_query_fields = {
        'verb': 'post',
        'visible': {'$ne': False}
    }

    # Add the activity written on contexts where the user is subscribed
    subscribed_contexts_urls = [subscribed['url'] for subscribed in actor.get('subscribedTo', [])]
    context_activity_query = {
        'contexts.url': {
            '$in': subscribed_contexts_urls
        }
    }
    context_activity_query.update(common_query_fields)

    # Add the activity of the people that the user follows
    followed_usernames = [followed['username'] for followed in actor.get('following', [])]
    # Include the requesting actor as another followed user
    followed_usernames.append(actor['username'])
    followed_users_activity_query = {
        'actor.username': {
            '$in': followed_usernames
        }
    }
    followed_users_activity_query.update(common_query_fields)

    # Construct the final $or query. followed_users_activity_query will never be empty, as it will always
    # include the requesting username. Subscribed contexts may be empty.
    or_queries = [followed_users_activity_query]
    if subscribed_contexts_urls:
        or_queries.append(context_activity_query)

    query = {
        "$or": or_queries
    }
    return query


@endpoint(route_name='timeline', request_method='GET', permission=view_timeline)
def getUserTimeline(user, request):
    """
        Get user timeline
    """
    query = timelineQuery(user)

    activities = sorted_query(request, request.db.activity, query, flatten=1)

    handler = JSONResourceRoot(request, activities)
    return handler.buildResponse()


@endpoint(route_name='timeline_authors', request_method='GET', permission=view_timeline)
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
            query = {'username': activity['actor']['username']}
            users = request.db.users.search(query, show_fields=["username"], sort_by_field="username", flatten=1)
            user = users.get()
            if user != []:
                distinct_authors.append(activity['actor'])
                distinct_usernames.append(activity['actor']['username'])

        if len(distinct_usernames) == author_limit:
            break

    is_head = request.method == 'HEAD'
    data = len(distinct_usernames) if is_head else distinct_authors

    handler = JSONResourceRoot(request, data, stats=is_head)
    return handler.buildResponse()
