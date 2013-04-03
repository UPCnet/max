# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pymongo import ASCENDING

from max.exceptions import ValidationError
from max.MADMax import MADMaxDB, MADMaxCollection
from max.models import Activity
from max.models import Conversation as Conversation
from max.decorators import MaxResponse, requirePersonActor
from max.oauth2 import oauth2

from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.rest.utils import extractPostData


@view_config(route_name='conversations', request_method='GET')
@MaxResponse
@requirePersonActor
@oauth2(['widgetcli'])
def getConversations(context, request):
    """
         /conversations
         Return all conversations depending on the actor requester
    """
    mmdb = MADMaxDB(context.db)
    query = {'participants': request.actor['username'],
             'objectType': 'conversation',
             }

    conversations = mmdb.conversations.search(query, sort="published", flatten=1, keep_private_fields=False)
    for conversation in conversations:
        query = {'objectType': 'message',
                 'contexts.hash': conversation['hash']
                 }
        messages = mmdb.messages.search(query, flatten=1)
        lastMessage = messages[-1]
        conversation['lastMessage'] = {'published': lastMessage['published'],
                                                 'content': lastMessage['object']['content']
                                                 }
        conversation['messages'] = len(messages)

    handler = JSONResourceRoot(sorted(conversations, reverse=True, key=lambda conv: conv['lastMessage']['published']))
    return handler.buildResponse()


@view_config(route_name='conversations', request_method='POST')
@MaxResponse
@requirePersonActor
@oauth2(['widgetcli'])
def postMessage2Conversation(context, request):
    """
         /conversations
         Post message to a conversation
    """

    # We are forced the check and extract the context of the conversation here,
    # We can't initialize the activity first, because it would fail (chiken-egg stuff)
    data = extractPostData(request)
    ctxts = data.get('contexts', [])
    if len(ctxts) == 0:
        raise ValidationError('Empty contexts parameter')
    if len(ctxts[0]['participants']) == 0:
        raise ValidationError('Empty participants parameter')

    #Loop trough all participants, if there's one that doesn't exists, an exception will raise
    #This check is to avoid any conversation creation if there's any invalid participant

    users = MADMaxCollection(context.db.users, query_key='username')
    for participant in ctxts[0]['participants']:
        user = users[participant]

    # If there are only two participants in the conversation, try to get an existing conversation
    # Otherwise, assume is a group conversation and create a new one
    current_conversation = None
    if len(ctxts[0]['participants']) == 2:
        contexts = MADMaxCollection(context.db.conversations)
        conversations = contexts.search({'objectType': 'conversation', 'participants': {'$in': ctxts[0]['participants']}})
        if conversations:
            current_conversation = conversations[0]

    if current_conversation is None:
        # Initialize a conversation (context) object from the request, overriding the object using the context
        conversation_params = dict(actor=request.actor,
                                   participants=ctxts[0]['participants'],
                                   permissions={'read': 'subscribed',
                                                'write': 'subscribed',
                                                'subscribe': 'restricted',
                                                'unsubscribe': 'public',
                                                'invite': 'restricted'}
                                   )
        newconversation = Conversation(request)
        newconversation.fromRequest(request, rest_params=conversation_params)

        if not request.actor.username in newconversation['participants']:
            raise ValidationError('Actor must be part of the participants list.')

        # New conversation
        contextid = newconversation.insert()
        newconversation['_id'] = contextid

        # Subscribe everyone,
        for user in newconversation['participants']:
            users[user].addSubscription(newconversation)

        current_conversation = newconversation

    # We have to re-get the actor, in order to have the subscription updated
    message_params = {'actor': users[request.actor['username']],
                      'contexts': [{'objectType': 'conversation',
                                    'hash': current_conversation.hash
                                    }],
                      'verb': 'post'}

    # Initialize a Message (Activity) object from the request
    newmessage = Activity(request)
    newmessage.fromRequest(request, rest_params=message_params)

    message_oid = newmessage.insert()
    newmessage['_id'] = message_oid

    handler = JSONResourceEntity(newmessage.flatten(), status_code=201)
    return handler.buildResponse()


@view_config(route_name='messages', request_method='GET')
@MaxResponse
@requirePersonActor
@oauth2(['widgetcli'])
def getMessages(context, request):
    """
         /conversations/{hash}/messages
         Return all messages from a conversation
    """
    chash = request.matchdict['hash']

    if chash not in [ctxt.get("hash", '') for ctxt in request.actor.subscribedTo.get("items", [])]:
        raise ValidationError('Actor must be either subscribed to the conversation or a participant of it.')

    mmdb = MADMaxDB(context.db)
    query = {'contexts.hash': chash}
    messages = mmdb.activity.search(query, sort="published", sort_dir=ASCENDING, flatten=1, keep_private_fields=False)

    handler = JSONResourceRoot(messages)
    return handler.buildResponse()


@view_config(route_name='messages', request_method='POST')
@MaxResponse
@requirePersonActor
@oauth2(['widgetcli'])
def addMessage(context, request):
    """
         /conversations/{hash}/messages
         Post a message to 1 (one) existing conversation
    """
    chash = request.matchdict['hash']
    message_params = {'actor': request.actor,
                      'verb': 'post',
                      'contexts': [{'objectType': 'conversation',
                                    'hash': chash
                                    }]
                      }

    # Initialize a Message (Activity) object from the request
    newmessage = Activity(request)
    newmessage.fromRequest(request, rest_params=message_params)

    message_oid = newmessage.insert()
    newmessage['_id'] = message_oid

    handler = JSONResourceEntity(newmessage.flatten(), status_code=201)
    return handler.buildResponse()
