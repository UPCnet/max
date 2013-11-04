# -*- coding: utf-8 -*-
from pyramid.view import view_config

from max.oauth2 import oauth2
from max.decorators import MaxResponse, requirePersonActor

from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot


@view_config(route_name='maintenance_keywords', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False, exists=False)
def rebuildKeywords(context, request):
    """
         /maintenance/keywords

         Rebuild keywords of all activities

    """
    mmdb = MADMaxDB(context.db)
    activities = mmdb.activity.dump()
    for activity in activities:
        activity.object.setKeywords()
        activity.setKeywords()
        activity.save()

    handler = JSONResourceRoot([])
    return handler.buildResponse()


@view_config(route_name='maintenance_subscriptions', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False, exists=False)
def rebuildSubscriptions(context, request):
    """
         /maintenance/subscriptions

         Rebuild subscriptions performing sanity checks

    """
    mmdb = MADMaxDB(context.db)

    existing_contexts = {}
    contexts = mmdb.contexts.dump()
    for context in contexts:
        context.updateUsersSubscriptions(force_update=True)
        context.updateContextActivities(force_update=True)
        existing_contexts[context['hash']] = context

    users = mmdb.users.search({'subscribedTo': {'$exists': True, '$size': {'$gt': 0}}})
    for user in users:
        for subscription in user.get('subscribedTo', []):
            if subscription['hash'] not in existing_contexts:
                user.unsubscribe(existing_contexts[subscription['hash']])
    handler = JSONResourceRoot([])
    return handler.buildResponse()


@view_config(route_name='maintenance_conversations', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False, exists=False)
def rebuildConversationSubscriptions(context, request):
    """
         /maintenance/conversations

         Rebuild conversation subscriptions performing sanity checks

    """
    mmdb = MADMaxDB(context.db)

    existing_conversations = {}
    conversations = mmdb.conversations.dump()
    for conversation in conversations:
        conversation.updateUsersSubscriptions(force_update=True)
        conversation.updateContextActivities(force_update=True)
        existing_conversations[conversation['_id']] = conversation

    users = mmdb.users.search({'talkingIn': {'$exists': True, '$size': {'$gt': 0}}})
    for user in users:
        for subscription in user.get('talkingIn', []):
            if subscription['id'] not in existing_conversations:
                user.unsubscribe(existing_conversations[subscription['id']])
    handler = JSONResourceRoot([])
    return handler.buildResponse()