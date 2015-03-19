# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.MADMax import MADMaxDB
from max.decorators import MaxResponse
from max.decorators import requirePersonActor
from max.exceptions import ObjectNotFound
from max.exceptions import Unauthorized
from max.models import Activity
from max.oauth2 import oauth2
from max.rest.ResourceHandlers import JSONResourceEntity
from max.rest.ResourceHandlers import JSONResourceRoot
from max.rest.utils import searchParams

from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config
from max import DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY
from max.exceptions import InvalidPermission
from max.security.permissions import add_subscription, remove_subscription, manage_subcription_permissions, view_subscriptions


@view_config(route_name='context_subscriptions', request_method='POST', requires_actor=True, permission=add_subscription)
def subscribe(context, request):
    """
        /context/{hash}/subscriptions

        Subscribe the actor to the suplied context.
    """
    actor = request.actor
    rest_params = {'object': context,
                   'verb': 'subscribe'}

    # Initialize a Activity object from the request
    newactivity = Activity()
    newactivity.fromRequest(request, rest_params=rest_params)

    # Check if user is already subscribed
    subscribed_contexts_hashes = [a['hash'] for a in actor.subscribedTo]
    if newactivity.object.getHash() in subscribed_contexts_hashes:
        # If user already subscribed, send a 200 code and retrieve the original subscribe activity
        # post when user was subscribed. This way in th return data we'll have the date of subscription
        code = 200
        activities = MADMaxCollection(request.db.activity)
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


@view_config(route_name='context_subscription', request_method='DELETE', requires_actor=True, permission=remove_subscription)
def unsubscribe(subscription, request):
    """
    """
    subscription.context.removeUserSubscriptions(users_to_delete=[request.actor_username])
    return HTTPNoContent()


@view_config(route_name='context_subscriptions', request_method='GET', requires_actor=True, permission=view_subscriptions)
def getContextSubscriptions(subscriptions, request):
    """
    """
    chash = request.matchdict['hash']
    mmdb = MADMaxDB(request.db)
    found_users = mmdb.users.search({"subscribedTo.hash": chash}, flatten=1, show_fields=["username", "subscribedTo"], **searchParams(request))
    for user in found_users:

        subscription = user['subscribedTo'][0]
        del user['subscribedTo']
        user['permissions'] = subscription.pop('permissions')
        user['vetos'] = subscription.pop('vetos', [])
        user['grants'] = subscription.pop('grants', [])

    handler = JSONResourceRoot(found_users)
    return handler.buildResponse()


@view_config(route_name='subscriptions', request_method='GET', requires_actor=True)
def getUserSubscriptions(context, request):
    """
        /people/{username}/subscriptions

        List all subscriptions for the the suplied oauth user.
    """

    search_params = searchParams(request)

    # XXX Remove when refactoring subscriptions storage to a different collection
    tags = set(search_params.pop('tags', []))

    mmdb = MADMaxDB(request.db)
    query = {'username': request.actor['username']}
    users = mmdb.users.search(query, preserve=["username", "subscribedTo"], flatten=1, **search_params)

    subscriptions = users[0]['subscribedTo'] if users else []

    # XXX Remove when refactoring subscriptions storage to a different collection
    if tags:
        filtered_subscriptions = []
        for subscription in subscriptions:
            if tags.intersection(set(subscription.get('tags', []))) == tags:
                filtered_subscriptions.append(subscription)
        subscriptions = filtered_subscriptions

    handler = JSONResourceRoot(subscriptions)
    return handler.buildResponse()


@view_config(route_name='context_user_permission', request_method='PUT', requires_actor=True, permission=manage_subcription_permissions)
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def grantPermissionOnContext(context, request):
    """ [RESTRICTED]
    """
    permission = request.matchdict.get('permission', None)
    if permission not in ['read', 'write', 'subscribe', 'invite', 'delete', 'flag']:
        raise InvalidPermission("There's not any permission named '%s'" % permission)

    chash = request.matchdict.get('hash', None)
    subscription = None
    pointer = 0
    while subscription is None and pointer < len(request.actor.subscribedTo):
        if request.actor.subscribedTo[pointer]['hash'] == chash:
            subscription = request.actor.subscribedTo[pointer]
        pointer += 1

    if not subscription:
        raise Unauthorized("You can't set permissions on a context where the user is not subscribed")

    # If we reach here, we are subscribed to a context and ready to set the permission

    if permission in subscription.get('_grants', []):
        # Already have the permission grant
        code = 200
    else:
        # Assign the permission
        code = 201
        subscription = request.actor.grantPermission(
            subscription,
            permission,
            permanent=request.params.get('permanent', DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY))

    handler = JSONResourceEntity(subscription, status_code=code)
    return handler.buildResponse()


@view_config(route_name='context_user_permission', request_method='DELETE', requires_actor=True, permission=manage_subcription_permissions)
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def revokePermissionOnContext(context, request):
    """ [RESTRICTED]
    """
    permission = request.matchdict.get('permission', None)
    if permission not in ['read', 'write', 'subscribe', 'invite', 'flag']:
        raise InvalidPermission("There's not any permission named '%s'" % permission)

    chash = request.matchdict.get('hash', None)
    subscription = None
    pointer = 0
    while subscription is None and pointer < len(request.actor.subscribedTo):
        if request.actor.subscribedTo[pointer]['hash'] == chash:
            subscription = request.actor.subscribedTo[pointer]
        pointer += 1

    if not subscription:
        raise Unauthorized("You can't remove permissions on a context where you are not subscribed")

    # If we reach here, we are subscribed to a context and ready to remove the permission

    code = 200
    if permission in subscription.get('_vetos', []):
        code = 200
        # Alredy vetted
    else:
        # We have the permission, let's delete it
        subscription = request.actor.revokePermission(
            subscription,
            permission,
            permanent=request.params.get('permanent', DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY))
        code = 201
    handler = JSONResourceEntity(subscription, status_code=code)
    return handler.buildResponse()


@view_config(route_name='context_user_permissions_defaults', request_method='POST', requires_actor=True, permission=manage_subcription_permissions)
def resetPermissionsOnContext(context, request):
    """ [RESTRICTED]
    """
    chash = request.matchdict.get('hash', None)
    subscription = None
    pointer = 0
    while subscription is None and pointer < len(request.actor.subscribedTo):
        if request.actor.subscribedTo[pointer]['hash'] == chash:
            subscription = request.actor.subscribedTo[pointer]
        pointer += 1

    if not subscription:
        raise Unauthorized("You can't set permissions on a context where the user is not subscribed")

    # If we reach here, we are subscribed to a context and ready to reset the permissions

    contexts = MADMaxCollection(request.db.contexts)
    maxcontext = contexts.getItemsByhash(chash)[0]
    subscription = request.actor.reset_permissions(subscription, maxcontext)
    handler = JSONResourceEntity(subscription, status_code=200)
    return handler.buildResponse()


