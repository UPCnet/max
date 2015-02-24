# -*- coding: utf-8 -*-
from max.rest.utils import searchParams


# sort_strategy: A prefefined string identifying a sort strategy
#     Currently supports:
#         recent: Sorts by publishing/commenting date defined in sort_priority selection
#         flag: Sorts by flag date, using sort_priority date as second sort order
#         likes: Sorts by number of activity likes, using sort_priority date as second sort order
# sort_priority: Defines if date sorting is based on activity date or last comment date

# Here we define the different known methods to sort objects, grouped py
# the method name used externally. Each method MUST define a diferent set of
# sort parameters for each sort_priority that the system recongnizes.

from pymongo import DESCENDING

SORT_STRATEGIES = {
    'published': {
        'activity': [('_id', DESCENDING)],
        'comments': [('lastComment', DESCENDING)]
    },
    'flagged': {
        'activity': [('flagged', DESCENDING), ('_id', DESCENDING)],
        'comments': [('flagged', DESCENDING), ('lastComment', DESCENDING)]
    },
    'likes': {
        'activity': [('likesCount', DESCENDING), ('lastLike', DESCENDING)],
        'comments': [('likesCount', DESCENDING), ('lastComment', DESCENDING)],
    }
}


def sorted_query(request, collection, query, **kwargs):
    """
        Main sort method that determines which method of sorting to use
        based on sort parameters found in the request.

        Falls back to sensible defaults if no sorting defined
    """
    search_params = searchParams(request)
    search_params.update(kwargs)
    is_head = request.method == 'HEAD'
    strategy = search_params.pop('sort_strategy', 'published')
    priority = search_params.pop('sort_priority', 'activity')

    search_params['sort_params'] = SORT_STRATEGIES[strategy][priority]

    if strategy == 'published':
        activities = simple_sort(collection, query, search_params, is_head)

    elif strategy == 'likes':
        search_params['flatten'] = 1
        activities = get_activities_sorted_by_like_count(collection, query, search_params, is_head)

    elif strategy == 'flagged':
        search_params['flatten'] = 1
        activities = get_activities_sorted_by_flagged_first(collection, query, search_params, is_head)

    return activities


def simple_sort(collection, query, search_params, is_head):
    return collection.search(
        query,
        count=is_head,
        keep_private_fields=False,
        **search_params)


def get_activities_sorted_by_like_count(collection, query, search_params, is_head):
    """
        Sorts activities by likes Count. Activities without likes will appear
        sorted by descending activity published date order.

        Sorting is made by concatenating subqueries, and preserving coherence
        and order between pagination.

        There are 4 different queries that may be executed, depending on the scenario:

        - First page of a set of activities(with or without liked objects):
            - NEXT_LIKES_QUERY will get the top liked activities until the specified limit is reached
            - NO_LIKES_QUERY will fill up until specified limit ONLY if limit not reached in previous query

        - Second and following pages of a set of activies(with or without liked objects):
            - LAST_ITEM_QUERY will search for the last item of the previous page
            - SAME_LIKES_QUERY will find ALL activities with the same number of likes of
              the last item
            - NEXT_LIKES_QUERY will search for activities with less likes than the last items ONLY
              if limit is not reached
            - NO_LIKES_QUERY will fill up until specified limit ONLY if limit not reached in previous query

        So the most expensive scenario is the one that in a non-first page, has mixed elements,
        that could execute 4 queries.

    """
    # This var controls whether if we have to look for liked
    # items. We alway look for them on first page, not always on 2+ pages
    do_search_liked = True
    last_page_had_likes = True
    last = None

    activities = []

    # Enhance the query to filter the activities,
    # getting only the ones that have been liked
    query['likesCount'] = {'$exists': 1, '$ne': 0}

    # If we are in a 2+ page
    if 'before' in search_params:
        # Get the last object of the previous page...
        # QUERY ID: LAST_ITEM_QUERY
        last = collection[search_params['before']]
        search_params['before'] = None

        # If the last object has no likes, do nothing
        if not last.get('likesCount', 0):
            do_search_liked = False
            last_page_had_likes = False
        # Otherwise continue processing
        else:
            # The problem is that in order to get the next page of items, we have to request
            # first of all the items with likesCount == last.likesCount
            query['likesCount']['$eq'] = last['likesCount']
            same_likesCount_search_params = dict(search_params)
            del same_likesCount_search_params['limit']
            # QUERY ID: SAME_LIKES_QUERY
            same_likesCount_activities = collection.search(
                query,
                count=is_head,
                offset_field='lastLike',
                keep_private_fields=False,
                **same_likesCount_search_params)

            # and discard all of them until the last displayed item is found
            # The remaining items will be items with the same like_count not displayed already
            for activity_index, activity in enumerate(same_likesCount_activities):
                if activity['id'] == str(last['_id']):
                    break

            same_likesCount_activities = same_likesCount_activities[activity_index + 1:]

            # If we have enough results to fullfill the limit requested, we don't
            # need to query more liked items
            if len(same_likesCount_activities) >= search_params['limit']:
                activities = same_likesCount_activities[:search_params['limit']]
                do_search_liked = False

            # If we don't have enough items and we last queryied for likesCount == 1
            # we don't need to query more liked items, because we used all activities
            # with a positive value in likesCount
            elif last['likesCount'] == 1:
                activities = same_likesCount_activities
                do_search_liked = False

            # Otherwise, configure next query to keep searching for items
            # with less likesCount
            else:
                activities = same_likesCount_activities
                del query['likesCount']['$eq']
                query['likesCount']['$lt'] = last['likesCount']

    if do_search_liked:
        # QUERY ID: NEXT_LIKES_QUERY
        activities += collection.search(
            query,
            count=is_head,
            offset_field='lastLike',
            keep_private_fields=False,
            **search_params)

    # Use case 1:
    # - We requested <limit> liked activities, and we got zero or less than <limit
    #   In this situation, fill up to <limit> with the rest of non-liked actities
    #  Use case 2:
    # - We didn't request any liked activity because we're in a  2+ page that has no
    #   liked activities
    if len(activities) < search_params['limit']:
        # Search non-liked activities to fullfill <limit> requirement
        query.pop('likesCount', None)
        query['likesCount'] = 0
        # (Use case 2) Filter by the last displayed
        search_params['sort_order'] = 'activities'
        if not last_page_had_likes:
            search_params['before'] = last._id

        # QUERY ID: NO_LIKES_QUERY
        search_params['sort_params'] = SORT_STRATEGIES['published']['activity']
        non_liked_activities = collection.search(
            query,
            count=is_head,
            keep_private_fields=False,
            **search_params)
        needed = search_params['limit'] - len(activities)
        activities += non_liked_activities[:needed]

    return activities


def get_activities_sorted_by_flagged_first(collection, query, search_params, is_head):
    """
    """
    # This var controls whether if we have to look for flagged
    # items. We alway look for them on first page, not aloways on 2+ pages
    do_search_flagged = True
    activities = []

    # Enchange the query to filter the activities,
    # getting only the ones that have been flagged
    query['flagged'] = {'$exists': 1, '$ne': None}

    # If we are in a 2+ page
    if 'before' in search_params:
        # Get the last object of the previous page...
        last = collection[search_params['before']]
        search_params['before'] = None
        #... and if that item displayed is flagged it means
        # that we may have more flagged items to display
        if last.get('flagged', None):
            query['flagged']['$lt'] = last['flagged']
        else:
            do_search_flagged = False

    if do_search_flagged:
        activities = collection.search(query, count=is_head, keep_private_fields=False, **search_params)

    # Use case 1:
    # - We requested <limit> flagged activities, and we got zero or less than <limit
    #   In this situation, fill up to <limit> with the rest of non-flagged actities
    #  Use case 2:
    # - We did'nt request any flagged activity because we're in a  2+ page that has no
    #   flagged activities
    if len(activities) < search_params['limit']:
        # Search non-flagged activities to fullfill <limit> requirement
        query.pop('flagged', None)
        query['flagged'] = {'$exists': 0}
        # (Use case 2) Filter by the last displayed
        if not do_search_flagged:
            search_params['before'] = last._id

        search_params['sort_params'] = SORT_STRATEGIES['published']['activity']
        non_flagged_activities = collection.search(
            query,
            count=is_head,
            keep_private_fields=False,
            **search_params)
        needed = search_params['limit'] - len(activities)
        activities += non_flagged_activities[:needed]

    return activities
