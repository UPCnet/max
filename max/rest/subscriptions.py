# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.models import Activity
from max.rest.ResourceHandlers import JSONResourceEntity
from max.rest.ResourceHandlers import JSONResourceRoot
from max.rest.utils import searchParams

from pyramid.httpexceptions import HTTPNoContent
from max.rest import endpoint
from max import DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY
from max import DEFAULT_CONTEXT_PERMISSIONS
from max.exceptions import InvalidPermission
from max.security.permissions import add_subscription, remove_subscription, manage_subcription_permissions, view_subscriptions


@endpoint(route_name='context_subscriptions', request_method='POST', requires_actor=True, permission=add_subscription)
def subscribe(context, request):
    """
        /context/{hash}/subscriptions

        Subscribe the actor to the suplied context.
    """
    actor = request.actor
    rest_params = {'object': context,
                   'verb': 'subscribe'}

    # Initialize a Activity object from the request
    newactivity = Activity.from_request(request, rest_params=rest_params)

    # Check if user is already subscribed
    subscribed_contexts_hashes = [a['hash'] for a in actor.subscribedTo]
    if newactivity.object.getHash() in subscribed_contexts_hashes:
        # If user already subscribed, send a 200 code and retrieve the original subscribe activity
        # post when user was subscribed. This way in th return data we'll have the date of subscription
        code = 200
        activities = MADMaxCollection(request, 'activity')
        query = {'verb': 'subscribe', 'object.url': newactivity.object['url'], 'actor.username': actor.username}
        newactivity = activities.search(query)[-1]  # Pick the last one, so we get the last time user subscribed (in cas a unsbuscription occured sometime...)

    else:
        actor.addSubscription(context)

        # If user wasn't created, 201 will show that the subscription has just been added
        code = 201
        newactivity_oid = newactivity.insert()  # Insert a subscribe activity
        newactivity['_id'] = newactivity_oid
    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@endpoint(route_name='context_subscription', request_method='DELETE', requires_actor=True, permission=remove_subscription)
def unsubscribe(context, request):
    """
    """
    context.removeUserSubscriptions(users_to_delete=[request.actor_username])
    return HTTPNoContent()


@endpoint(route_name='context_subscriptions', request_method='GET', requires_actor=True, permission=view_subscriptions)
def getContextSubscriptions(context, request):
    """
    """
    found_users = request.db.users.search({"subscribedTo.hash": context['hash']}, flatten=1, show_fields=["username", "subscribedTo"], **searchParams(request))
    for user in found_users:
        subscription = user['subscribedTo'][0]
        del user['subscribedTo']
        user['permissions'] = subscription.pop('permissions')
        user['vetos'] = subscription.pop('vetos', [])
        user['grants'] = subscription.pop('grants', [])

    handler = JSONResourceRoot(found_users)
    return handler.buildResponse()


@endpoint(route_name='subscriptions', request_method='GET', requires_actor=True, permission=view_subscriptions)
def getUserSubscriptions(user, request):
    """
        /people/{username}/subscriptions

        List all subscriptions for the the suplied oauth user.
    """
    subscriptions = user.get('subscribedTo', [])

    search_params = searchParams(request)
    tags = set(search_params.pop('tags', []))

    # XXX Whhen refactoring subscriptions storage to a different collection
    # Change this for a search on subscriptions collection
    if tags:
        filtered_subscriptions = []
        for subscription in subscriptions:
            if tags.intersection(set(subscription.get('tags', []))) == tags:
                filtered_subscriptions.append(subscription)
        subscriptions = filtered_subscriptions

    handler = JSONResourceRoot(subscriptions)
    return handler.buildResponse()


@endpoint(route_name='context_user_permission', request_method='PUT', requires_actor=True, permission=manage_subcription_permissions)
def grantPermissionOnContext(context, request):
    """ [RESTRICTED]
    """
    permission = request.matchdict.get('permission', None)
    if permission not in DEFAULT_CONTEXT_PERMISSIONS.keys():
        raise InvalidPermission("There's not any permission named '%s'" % permission)

    if permission in context.subscription.get('_grants', []):
        # Already have the permission grant
        code = 200
    else:
        # Assign the permission
        code = 201
        subscription = request.actor.grantPermission(
            context.subscription,
            permission,
            permanent=request.params.get('permanent', DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY))

    handler = JSONResourceEntity(subscription, status_code=code)
    return handler.buildResponse()


@endpoint(route_name='context_user_permission', request_method='DELETE', requires_actor=True, permission=manage_subcription_permissions)
def revokePermissionOnContext(context, request):
    """
    """
    permission = request.matchdict.get('permission', None)
    if permission not in DEFAULT_CONTEXT_PERMISSIONS.keys():
        raise InvalidPermission("There's not any permission named '%s'" % permission)

    code = 200
    if permission in context.subscription.get('_vetos', []):
        code = 200
        # Alredy vetted
    else:
        # We have the permission, let's delete it
        subscription = request.actor.revokePermission(
            context.subscription,
            permission,
            permanent=request.params.get('permanent', DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY))
        code = 201
    handler = JSONResourceEntity(subscription, status_code=code)
    return handler.buildResponse()


@endpoint(route_name='context_user_permissions_defaults', request_method='POST', requires_actor=True, permission=manage_subcription_permissions)
def resetPermissionsOnContext(context, request):
    """
    """

    subscription = request.actor.reset_permissions(context.subscription, context)
    handler = JSONResourceEntity(subscription, status_code=200)
    return handler.buildResponse()
