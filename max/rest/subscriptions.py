# -*- coding: utf-8 -*-
from max import DEFAULT_CONTEXT_PERMISSIONS
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


@view_config(route_name='subscriptions', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=True)
def getUserSubscriptions(context, request):
    """
        /people/{username}/subscriptions

        List all subscriptions for the the suplied oauth user.
    """

    search_params = searchParams(request)

    # XXX Remove when refactoring subscriptions storage to a different collection
    tags = set(search_params.pop('tags', []))

    mmdb = MADMaxDB(context.db)
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


@view_config(route_name='subscriptions', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=True)
def subscribe(context, request):
    """
        /people/{username}/subscriptions

        Subscribe the actor to the suplied context.
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
    if newactivity.object.getHash() in subscribed_contexts_hashes:
        # If user already subscribed, send a 200 code and retrieve the original subscribe activity
        # post when user was subscribed. This way in th return data we'll have the date of subscription
        code = 200
        activities = MADMaxCollection(context.db.activity)
        query = {'verb': 'subscribe', 'object.url': newactivity.object['url'], 'actor.username': actor.username}
        newactivity = activities.search(query)[-1]  # Pick the last one, so we get the last time user subscribed (in cas a unsbuscription occured sometime...)

    else:

        #Register subscription to the actor
        contexts = MADMaxCollection(context.db.contexts, query_key='hash')
        scontext = contexts[newactivity['object'].getHash()]
        if scontext.permissions.get('subscribe', DEFAULT_CONTEXT_PERMISSIONS['subscribe']) == 'restricted':
            raise Unauthorized('User {0} cannot subscribe himself to to this context'.format(actor['username']))
        actor.addSubscription(scontext)

        # If user wasn't created, 201 will show that the subscription has just been added
        code = 201
        newactivity_oid = newactivity.insert()  # Insert a subscribe activity
        newactivity['_id'] = newactivity_oid
    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='subscription', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=True)
def unsubscribe(context, request):
    """
    """
    actor = request.actor
    mmdb = MADMaxDB(context.db)
    chash = request.matchdict.get('hash', None)
    subscription = actor.getSubscription({'hash': chash, 'objectType': 'context'})

    if subscription is None:
        raise ObjectNotFound("User {0} is not subscribed to context with hash: {1}".format(actor.username, chash))

    if 'unsubscribe' not in subscription.get('permissions', []):
        raise Unauthorized('User {0} cannot unsubscribe himself from this context'.format(actor.username))

    found_context = mmdb.contexts.getItemsByhash(chash)

    found_context[0].removeUserSubscriptions(users_to_delete=[actor.username])
    return HTTPNoContent()
