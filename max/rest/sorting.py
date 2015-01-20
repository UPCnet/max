# -*- coding: utf-8 -*-
from max.rest.utils import searchParams


def get_activities_sorted_by_date(request, mmdb, query, is_head=False):
    """
    """
    return mmdb.activity.search(query, count=is_head, sort='_id', flatten=1, keep_private_fields=False, **searchParams(request))


def get_activities_sorted_by_last_comment_date(request, mmdb, query, is_head=False):
    """
    """
    return mmdb.activity.search(query, count=is_head, sort='lastComment', flatten=1, keep_private_fields=False, **searchParams(request))


def get_activities_sorted_by_like_count(request, mmdb, query, is_head=False):
    """
    """
    search_params = searchParams(request)
    # If we're in a 2+ page of likes
    if 'before' in search_params and 'limit' in search_params:
        # Get the likes Count of the last object of the previous page
        last_page_object = mmdb.activity.search({'_id': search_params['before']})
        likes_count = last_page_object[0].likesCount
        # Target query to search items including the ones with the same likesCount than the last object
        # Widen the limit of resuts to the double as we may get duplicated results that we'll have to filter out later
        # the item referenced in before param will be included in the results of this search
        search_params['offset'] = likes_count + 1
        original_limit = int(search_params['limit'])
        search_params['limit'] = search_params['limit'] * 2

    activities = mmdb.activity.search(query, count=is_head, sort='likesCount', flatten=1, keep_private_fields=False, **searchParams(request))

    # If we're in a 2+ page of likes, continue filtering
    if 'before' in search_params and 'limit' in search_params:
        start = 0
        for pos, activity in enumerate(activities):
            if activity['id'] == str(search_params['before']):
                # We found the object referenced in before param, so we pick the next item as the first
                start = pos + 1
                break
        # Pick activities according to the original limit, excluding the ones included in the latest page
        activities = activities[start:start + original_limit]

    return activities


def get_activities_sorted_by_flagged_first(request, mmdb, query, is_head=False):
    """
    """
    # This var controls whether if we have to look for flagged
    # items. We alway look for them on first page, not aloways on 2+ pages
    do_search_flagged = True
    activities = []
    search_params = searchParams(request)

    # Enchange the query to filter the activities,
    # getting only the ones that have been flagged
    query['flagged'] = {'$exists': 1, '$ne': None}

    # If we are in a 2+ page
    if 'before' in search_params:
        # Get the last object of the previous page...
        last = mmdb.activity[search_params['before']]
        search_params['before'] = None
        #... and if that item displayed is flagged it means
        # that we may have more flagged items to display
        if last.get('flagged', None):
            query['flagged']['$lt'] = last['flagged']
        else:
            do_search_flagged = False

    if do_search_flagged:
        activities = mmdb.activity.search(query, count=is_head, sort='flagged', flatten=1, keep_private_fields=False, **search_params)

    # Use case 1:
    # - We requested <limit> flagged activities, and we got zero or less than <limit
    #   In this situation, fill up to <limit> with the rest of non-flagged actities
    #  Use case 2:
    # - We did'nt request any flagged activity because we're in a  2+ page that has no
    #   flagged activities
    if len(activities) < search_params['limit']:
        # Search non-flagged activities to fullfill <limit> requirement
        query.pop('flagged', None)
        query['flagged'] = {'$eq': None}
        # (Use case 2) Filter by the last displayed
        search_params['sort_order'] = 'activities'
        if not do_search_flagged:
            search_params['before'] = last._id

        non_flagged_activities = mmdb.activity.search(query, count=is_head, sort='_id', flatten=1, keep_private_fields=False, **search_params)
        needed = search_params['limit'] - len(activities)
        activities += non_flagged_activities[:needed]

    return activities


SORT_METHODS = {
    'activities': get_activities_sorted_by_date,
    'comments': get_activities_sorted_by_last_comment_date,
    'likes': get_activities_sorted_by_like_count,
    'flagged': get_activities_sorted_by_flagged_first
}
