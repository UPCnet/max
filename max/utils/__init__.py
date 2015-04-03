# -*- coding: utf-8 -*-
from max.exceptions import InvalidSearchParams
from max.utils.dates import date_filter_parser

from pyramid.settings import asbool

from bson.objectid import ObjectId

import re
import sys


def getMaxModelByObjectType(objectType):
    return getattr(sys.modules['max.models'], objectType.capitalize(), None)


def searchParams(request):
    """
        Extracts valid search params from the request, or sets default values if not found
        Returns a dict with all the results
        Raises InvalidSearchParams on bad param values
    """
    params = {}

    # KEEP For compatibility with older max, that did'nt distinguish
    # between sort order and sort priority. "sortBy" param will be translated
    # to sort_params

    deprecated_sort_by = request.params.get('sortBy', None)

    if deprecated_sort_by == 'activities':
        params['sort_strategy'] = 'published'
        params['sort_priority'] = 'activity'
    elif deprecated_sort_by == 'comments':
        params['sort_strategy'] = 'published'
        params['sort_priority'] = 'comments'
    elif deprecated_sort_by == 'likes':
        params['sort_strategy'] = 'likes'
        params['sort_priority'] = 'activity'
    elif deprecated_sort_by == 'flagged':
        params['sort_strategy'] = 'flagged'
        params['sort_priority'] = 'activity'

    sort_order = request.params.get('sort', None)
    if sort_order:
        params['sort_strategy'] = sort_order
        params['sort_priority'] = request.params.get('priority', 'activity')

    limit = request.params.get('limit', 10)
    try:
        limit = int(limit)
    except:
        raise InvalidSearchParams('limit must be a positive integer')
    else:
        if limit:
            params['limit'] = limit

    after = request.params.get('after')
    if after:
        try:
            params['after'] = ObjectId(after)
        except:
            raise InvalidSearchParams('after must be a valid ObjectId BSON identifier')

    before = request.params.get('before')
    if before:
        try:
            params['before'] = ObjectId(before)
        except:
            raise InvalidSearchParams('before must be a valid ObjectId BSON identifier')

    if 'before' in params and 'after' in params:
        raise InvalidSearchParams('only one offset filter is allowed, after or before')

    if 'date_filter' in request.params:
        date_filter = date_filter_parser(request.params.get('date_filter', ''))
        if date_filter:
            params['date_filter'] = date_filter

    hashtags = request.params.getall('hashtag')
    if hashtags:
        params['hashtag'] = [hasht.lower() for hasht in hashtags]

    actor = request.params.get('actor')
    if actor:
        params['actor'] = actor.lower().rstrip()

    keywords = request.params.getall('keyword')
    if keywords:
        # XXX Split or regex?
        params['keywords'] = [keyw.lower() for keyw in keywords]

    username = request.params.get('username')
    if username:
        params['username'] = username.lower()

    tags = request.params.getall('tags')
    if tags:
        retags = []
        for tag in tags:
            retag = re.sub(r'\s*(\w+)\s*', r'\1', tag, re.UNICODE)
            if retag:
                retags.append(retag)
        params['tags'] = retags

    favorites = request.params.get('favorites')
    if asbool(favorites):
        params['favorites'] = request.actor.username

    context_tags = request.params.getall('context_tags')
    if context_tags:
        retags = []
        for tag in context_tags:
            retag = re.sub(r'\s*(\w+)\s*', r'\1', tag, re.UNICODE)
            if retag:
                retags.append(retag)
        params['context_tags'] = retags

    twitter_enabled = request.params.get('twitter_enabled')
    if twitter_enabled:
        params['twitter_enabled'] = twitter_enabled

    show_fields = request.params.get('show_fields')
    if show_fields:
        params['show_fields'] = re.findall(r'\w+', show_fields)

    return params


def hasPermission(subscription, permission):
    """
        Determines if the subscription has a permission.
        If there's a revoked, permission this invalides any plain_permission.
        A granted permission oversees any revoke permission
    """
    permissions = subscription.get('permissions', [])
    has_plain_permission = permission in permissions
    has_granted_permission = permission in subscription.get('_grants', [])
    has_revoked_permission = permission in subscription.get('_grants', [])
    return (has_plain_permission and not has_revoked_permission) or has_granted_permission
