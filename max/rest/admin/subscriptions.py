# -*- coding: utf-8 -*-
from max import DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY
from max.MADMax import MADMaxCollection
from max.MADMax import MADMaxDB
from max.decorators import MaxResponse
from max.decorators import requirePersonActor
from max.exceptions import InvalidPermission
from max.exceptions import ObjectNotFound
from max.exceptions import Unauthorized
from max.models import Activity
from max.oauth2 import oauth2
from max.rest.utils import searchParams
from max.rest.ResourceHandlers import JSONResourceEntity, JSONResourceRoot

from pyramid.httpexceptions import HTTPNoContent
from pyramid.view import view_config

from hashlib import sha1


@view_config(route_name='subscriptions', request_method='POST', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def subscribe(context, request):
    """
        /people/{username}/subscriptions

        [RESTRICTED] Subscribe an username to the suplied context.
    """
    # XXX For now only one context can be subscribed at a time
    actor = request.actor
    rest_params = {'actor': actor,
                   'verb': 'subscribe'}

    # Initialize a Activity object from the request
    newactivity = Activity()
    newactivity.fromRequest(request, rest_params=rest_params)

    #Check if user is already subscribed
    subscribed_contexts_hashes = [a['hash'] for a in actor.subscribedTo]
    chash = sha1(newactivity.object['url']).hexdigest()
    if chash in subscribed_contexts_hashes:
        # If user already subscribed, send a 200 code and retrieve the original subscribe activity
        # post when user was subscribed. This way in th return data we'll have the date of subscription
        code = 200
        activities = MADMaxCollection(context.db.activity)
        query = {'verb': 'subscribe', 'object.url': newactivity.object['url'], 'actor.username': actor.username}
        newactivity = activities.search(query)[-1]  # Pick the last one, so we get the last time user subscribed (in cas a unsbuscription occured sometime...)

    else:
        # If user wasn't created, 201 indicates that the subscription has just been added
        code = 201
        newactivity_oid = newactivity.insert()  # Insert a subscribe activity
        newactivity['_id'] = newactivity_oid

        #Register subscription to the actor
        contexts = MADMaxCollection(context.db.contexts, query_key='hash')
        scontext = contexts[chash]
        actor.addSubscription(scontext)

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='subscription', request_method='DELETE', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def unsubscribe(context, request):
    """
        Unconditionally unsubscribe user from context
    """
    actor = request.actor
    mmdb = MADMaxDB(context.db)
    chash = request.matchdict.get('hash', None)
    subscription = actor.getSubscription({'hash': chash, 'objectType': 'context'})

    if subscription is None:
        raise ObjectNotFound("User {0} is not subscribed to context with hash: {1}".format(actor.username, chash))

    found_context = mmdb.contexts.getItemsByhash(chash)

    found_context[0].removeUserSubscriptions(users_to_delete=[actor.username])
    return HTTPNoContent()


@view_config(route_name='context_user_permission', request_method='PUT', restricted='Manager')
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


@view_config(route_name='context_user_permission', request_method='DELETE', restricted='Manager')
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


@view_config(route_name='context_user_permissions_defaults', request_method='POST', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
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

    contexts = MADMaxCollection(context.db.contexts)
    maxcontext = contexts.getItemsByhash(chash)[0]
    subscription = request.actor.reset_permissions(subscription, maxcontext)
    handler = JSONResourceEntity(subscription, status_code=200)
    return handler.buildResponse()


@view_config(route_name='context_subscriptions', request_method='GET', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def getContextSubscriptions(context, request):
    """
    """
    chash = request.matchdict['hash']
    mmdb = MADMaxDB(context.db)
    found_users = mmdb.users.search({"subscribedTo.hash": chash}, flatten=1, show_fields=["username", "subscribedTo"], **searchParams(request))

    for user in found_users:
        subscription = user['subscribedTo'][0]
        del user['subscribedTo']
        user['permissions'] = subscription.pop('permissions')
        user['vetos'] = subscription.pop('vetos', [])
        user['grants'] = subscription.pop('grants', [])

    handler = JSONResourceRoot(found_users)
    return handler.buildResponse()
