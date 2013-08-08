# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent

from max.exceptions import ObjectNotFound
from max.oauth2 import oauth2
from max.decorators import MaxResponse, requirePersonActor
from max.MADMax import MADMaxCollection
from max.models import Activity
from max.rest.ResourceHandlers import JSONResourceEntity
from max.MADMax import MADMaxDB
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
        # post when user was susbcribed. This way in th return data we'll have the date of subscription
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
