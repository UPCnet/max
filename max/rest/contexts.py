# -*- coding: utf-8 -*-
from max import AUTHORS_SEARCH_MAX_QUERIES_LIMIT
from max import LAST_AUTHORS_LIMIT
from max.exceptions import ObjectNotFound
from max.exceptions import ValidationError
from max.models import Context
from max.rest import JSONResourceEntity
from max.rest import JSONResourceRoot
from max.rest import endpoint
from max.rest.sorting import sorted_query
from max.utils.dicts import flatten
from max.utils import searchParams
from max.security.permissions import add_context
from max.security.permissions import delete_context
from max.security.permissions import list_activities
from max.security.permissions import list_contexts
from max.security.permissions import list_public_contexts
from max.security.permissions import modify_context
from max.security.permissions import view_context

from pyramid.httpexceptions import HTTPNoContent


@endpoint(route_name='contexts', request_method='GET', permission=list_contexts)
def getContexts(contexts, request):
    """
        Get all contexts
    """
    found_contexts = contexts.search({}, flatten=1, **searchParams(request))
    handler = JSONResourceRoot(found_contexts)
    return handler.buildResponse()


@endpoint(route_name='contexts', request_method='POST', permission=add_context)
def addContext(contexts, request):
    """
        Adds a context
    """
    # Initialize a Context object from the request
    newcontext = Context.from_request(request)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newcontext.get('_id'):
        # Already Exists
        code = 200
    else:
        # New context
        code = 201
        contextid = newcontext.insert()
        newcontext['_id'] = contextid

    handler = JSONResourceEntity(request, newcontext.flatten(), status_code=code)
    return handler.buildResponse()


@endpoint(route_name='context', request_method='GET', permission=view_context)
def getContext(context, request):
    """
        Get a context
    """
    handler = JSONResourceEntity(request, context.getInfo())
    return handler.buildResponse()


@endpoint(route_name='context', request_method='PUT', permission=modify_context)
def ModifyContext(context, request):
    """
        Modify a context
    """
    properties = context.getMutablePropertiesFromRequest(request)
    context.modifyContext(properties)
    context.updateUsersSubscriptions()
    context.updateContextActivities()
    handler = JSONResourceEntity(request, context.flatten())
    return handler.buildResponse()


@endpoint(route_name='context', request_method='DELETE', permission=delete_context)
def DeleteContext(context, request):
    """
        Delete a context
    """
    context.removeUserSubscriptions()
    context.removeActivities(logical=True)
    context.delete()
    return HTTPNoContent()


@endpoint(route_name='context_tags', request_method='GET', permission=view_context)
def getContextTags(context, request):
    """
        Get context tags
    """
    handler = JSONResourceRoot(context['tags'])
    return handler.buildResponse()


@endpoint(route_name='context_tags', request_method='DELETE', permission=modify_context)
def clearContextTags(context, request):
    """
        Delete all context tags
    """
    context['tags'] = []
    context.save()
    context.updateContextActivities(force_update=True)
    context.updateUsersSubscriptions(force_update=True)
    handler = JSONResourceRoot([])
    return handler.buildResponse()


@endpoint(route_name='context_tags', request_method='PUT', permission=modify_context)
def updateContextTags(context, request):
    """
        Add context tags
    """
    tags = request.decoded_payload

    # Validate tags is a list of strings
    valid_tags = isinstance(tags, list)
    if valid_tags:
        valid_tags = False not in [isinstance(tag, (str, unicode)) for tag in tags]
    if not valid_tags:
        raise ValidationError("Sorry, We're expecting a list of strings...")

    context['tags'].extend(tags)
    context['tags'] = list(set(context['tags']))
    context.save()
    context.updateContextActivities(force_update=True)
    context.updateUsersSubscriptions(force_update=True)
    handler = JSONResourceRoot(context['tags'])
    return handler.buildResponse()


@endpoint(route_name='context_tag', request_method='DELETE', permission=modify_context)
def removeContextTag(context, request):
    """
        Delete context tags
    """
    tag = request.matchdict['tag']

    try:
        context['tags'].remove(tag)
    except ValueError:
        raise ObjectNotFound('This context has no tag "{}"'.format(tag))

    context.save()
    context.updateContextActivities(force_update=True)
    context.updateUsersSubscriptions(force_update=True)
    return HTTPNoContent()


@endpoint(route_name='public_contexts', request_method='GET', permission=list_public_contexts)
def getPublicContexts(contexts, request):
    """
        Get all public contexts

        Returns a list of all public subscribable contexts
    """
    found_contexts = contexts.search({'permissions.subscribe': 'public'}, **searchParams(request))

    handler = JSONResourceRoot(flatten(found_contexts, squash=['owner', 'creator', 'published']))
    return handler.buildResponse()


@endpoint(route_name='context_activities_authors', request_method='GET', permission=list_activities)
def getContextAuthors(context, request):
    """
        Get context authors
    """
    chash = request.matchdict['hash']
    author_limit = int(request.params.get('limit', LAST_AUTHORS_LIMIT))

    query = {}
    query['contexts.hash'] = chash
    query['verb'] = 'post'
    # Include only visible activity, this includes activity with visible=True
    # and activity WITHOUT the visible field
    query['visible'] = {'$ne': False}

    still_has_activities = True

    # Save full author object to construct de response
    # and a separate username field to make the uniquefication easier
    distinct_authors = []
    distinct_usernames = []

    activities = None
    before = None
    queries = 0

    while len(distinct_usernames) < author_limit and still_has_activities and queries <= AUTHORS_SEARCH_MAX_QUERIES_LIMIT:
        try:
            # This can raise because the iterator is exhauste, or
            # or because on first iteration activities is None
            activity = activities.next()
        except:
            activity = None

        if not activity:
            extra = {'before': before} if before else {}
            activities = sorted_query(request, request.db.activity, query, **extra)
            activities_count = activities if isinstance(activities, int) else activities.cursor.count()
            queries += 1
            still_has_activities = activities_count > 0

        elif still_has_activities:

            before = activity['_id']
            if activity['actor']['username'] not in distinct_usernames:
                distinct_authors.append(activity['actor'])
                distinct_usernames.append(activity['actor']['username'])

    handler = JSONResourceRoot(distinct_authors)
    return handler.buildResponse()
