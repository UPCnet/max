# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent

from max import DEFAULT_CONTEXT_PERMISSIONS
from max.oauth2 import oauth2
from max.exceptions import Unauthorized, ObjectNotFound
from max.decorators import MaxResponse, requirePersonActor
from max.MADMax import MADMaxCollection
from max.models import Activity
from max.rest.ResourceHandlers import JSONResourceEntity
from max.MADMax import MADMaxDB
from max.rest.utils import searchParams
from max.rest.ResourceHandlers import JSONResourceRoot


@view_config(route_name='subscriptions', request_method='GET')
@MaxResponse
@requirePersonActor(force_own=True)
@oauth2(['widgetcli'])
def getUserSubscriptions(context, request):
    """
        /people/{username}/subscriptions

        List all subscriptions for the the suplied oauth user.
    """
    mmdb = MADMaxDB(context.db)
    query = {'username': request.actor['username']}
    users = mmdb.users.search(query, show_fields=["username", "subscribedTo"], flatten=1, **searchParams(request))

    if len(users) == 0:
        raise ObjectNotFound('User {0} is not subscribed to any context').format(request.actor['username'])
    handler = JSONResourceRoot(users[0]['subscribedTo']['items'])
    return handler.buildResponse()


@view_config(route_name='subscriptions', request_method='POST')
@MaxResponse
@requirePersonActor(force_own=True)
@oauth2(['widgetcli'])
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
    subscribed_contexts_hashes = [a['hash'] for a in actor.subscribedTo['items']]
    if newactivity.object.getHash() in subscribed_contexts_hashes:
        # If user already subscribed, send a 200 code and retrieve the original subscribe activity
        # post when user was susbcribed. This way in th return data we'll have the date of subscription
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
@requirePersonActor(force_own=True)
@oauth2(['widgetcli'])
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

    if not found_context:
        raise ObjectNotFound("There's no context matching this url hash: %s" % chash)

    found_context[0].removeUserSubscriptions(users_to_delete=[actor.username])
    return HTTPNoContent()


###################### Per comprovar els follows/unfollows al afegir, cal comprovar que no el segueixi previament


# @view_config(context=Root, request_method='POST', name="follow_context")
# def followContext(context, request):
#     # import ipdb; ipdb.set_trace()

#     try:
#         checkRequestConsistency(request)
#         data = extractPostData(request)
#     except:
#         return HTTPBadRequest()

#     try:
#         checkDataFollowContext(data)
#         checkIsValidUser(context, data)
#     except:
#         return HTTPBadRequest()

#     # Check if already follows

#     # Once verified the id of the users, convert their userid to an ObjectId
#     data['actor']['_id'] = ObjectId(data['actor']['id'])
#     del data['actor']['id']

#     # Set published date format
#     published = rfc3339(time.time())
#     data['published'] = published

#     # Insert activity in the database
#     context.db.activity.insert(data)

#     context.db.users.update({'_id': data['actor']['_id']},
#                             {'$push': {'subscribedTo.items': {'url': data['object']['url']}},
#                             '$inc': {'subscribedTo.totalItems': 1}})

#     return HTTPOk()


# @view_config(context=Root, request_method='POST', name="unfollow_context")
# def unFollowContext(context, request):
#     # import ipdb; ipdb.set_trace()
#     try:
#         checkRequestConsistency(request)
#         data = extractPostData(request)
#     except:
#         return HTTPBadRequest()

#     try:
#         checkDataunFollowContext(data)
#         checkIsValidUser(context, data)
#     except:
#         return HTTPBadRequest()

#     # Check if already not follows

#     # Once verified the id of the users, convert their userid to an ObjectId
#     data['actor']['_id'] = ObjectId(data['actor']['id'])
#     del data['actor']['id']

#     # Set published date format
#     published = rfc3339(time.time())
#     data['published'] = published

#     # Insert activity in the database
#     context.db.activity.insert(data)

#     context.db.users.update({'_id': data['actor']['_id']},
#                             {'$pull': {'subscribedTo.items': {'url': data['object']['url']}},
#                             '$inc': {'subscribedTo.totalItems': -1}})

#     return HTTPOk()
