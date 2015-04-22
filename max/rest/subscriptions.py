# -*- coding: utf-8 -*-
from max import DEFAULT_CONTEXT_PERMISSIONS
from max import DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY
from max.MADMax import MADMaxCollection
from max.exceptions import InvalidPermission
from max.models import Activity
from max.rest import JSONResourceEntity
from max.rest import JSONResourceRoot
from max.rest import endpoint
from max.utils import searchParams
from max.security.permissions import add_subscription
from max.security.permissions import manage_subcription_permissions
from max.security.permissions import remove_subscription
from max.security.permissions import view_subscriptions

from pyramid.httpexceptions import HTTPNoContent


@endpoint(route_name='context_subscriptions', request_method='POST', permission=add_subscription)
def subscribe(context, request):
    """
        Subscribe user to context
    """
    actor = request.actor
    rest_params = {'object': context,
                   'verb': 'subscribe'}

    # Initialize a Activity object from the request
    newactivity = Activity.from_request(request, rest_params=rest_params)

    # Check if user is already subscribed
    subscribed_contexts_hashes = [a['hash'] for a in actor['subscribedTo']]
    if newactivity['object'].getHash() in subscribed_contexts_hashes:
        # If user already subscribed, send a 200 code and retrieve the original subscribe activity
        # post when user was subscribed. This way in th return data we'll have the date of subscription
        code = 200
        activities = MADMaxCollection(request, 'activity')
        query = {'verb': 'subscribe', 'object.url': newactivity['object']['url'], 'actor.username': actor['username']}
        newactivity = activities.last(query)  # Pick the last one, so we get the last time user subscribed (in cas a unsbuscription occured sometime...)

    else:
        actor.addSubscription(context)

        # If user wasn't created, 201 will show that the subscription has just been added
        code = 201
        newactivity_oid = newactivity.insert()  # Insert a subscribe activity
        newactivity['_id'] = newactivity_oid
    handler = JSONResourceEntity(request, newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@endpoint(route_name='context_subscription', request_method='DELETE', permission=remove_subscription)
def unsubscribe(context, request):
    """
        Unsubscribe user from context
    """
    context.removeUserSubscriptions(users_to_delete=[request.actor_username])
    return HTTPNoContent()


@endpoint(route_name='context_subscriptions', request_method='GET', permission=view_subscriptions)
def getContextSubscriptions(context, request):
    """
        Get all context subscriptions
    """
    found_users = request.db.users.search({"subscribedTo.hash": context['hash']}, flatten=1, show_fields=["username", "subscribedTo"], **searchParams(request))

    def format_subscriptions():
        for user in found_users:
            subscription = user['subscribedTo'][0]
            del user['subscribedTo']
            user['permissions'] = subscription.pop('permissions')
            user['vetos'] = subscription.pop('vetos', [])
            user['grants'] = subscription.pop('grants', [])
            yield user

    handler = JSONResourceRoot(format_subscriptions())
    return handler.buildResponse()


@endpoint(route_name='subscriptions', request_method='GET', permission=view_subscriptions)
def getUserSubscriptions(user, request):
    """
        Get all user subscriptions
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


@endpoint(route_name='context_user_permission', request_method='PUT', permission=manage_subcription_permissions)
def grantPermissionOnContext(context, request):
    """
        Grant user permission on context
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

    handler = JSONResourceEntity(request, subscription, status_code=code)
    return handler.buildResponse()


@endpoint(route_name='context_user_permission', request_method='DELETE', permission=manage_subcription_permissions)
def revokePermissionOnContext(context, request):
    """
        Revoke user permission on context
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
    handler = JSONResourceEntity(request, subscription, status_code=code)
    return handler.buildResponse()


@endpoint(route_name='context_user_permissions_defaults', request_method='POST', permission=manage_subcription_permissions)
def resetPermissionsOnContext(context, request):
    """
        Reset user permissions on context
    """

    subscription = request.actor.reset_permissions(context.subscription, context)
    handler = JSONResourceEntity(request, subscription, status_code=200)
    return handler.buildResponse()
