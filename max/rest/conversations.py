# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pymongo import ASCENDING

from max.exceptions import ValidationError
from max.MADMax import MADMaxDB, MADMaxCollection
from max.models import Activity, Context
from max.ASObjects import Conversation
from max.decorators import MaxRequest, MaxResponse
from max.oauth2 import oauth2

from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.rest.utils import extractPostData


@view_config(route_name='conversations', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getConversations(context, request):
    """
         /conversations
         Return all conversations depending on the actor requester
    """
    mmdb = MADMaxDB(context.db)
    query = {'object.participants': request.actor['username'],
             'object.objectType': 'conversation',
             }

    conversations = mmdb.contexts.search(query, sort="published", flatten=1)
    for conversation in conversations:
        query = {'object.objectType': 'message',
                 'contexts.hash': conversation['hash']
                 }
        messages = mmdb.activity.search(query, flatten=1)
        lastMessage = messages[-1]
        conversation['object']['lastMessage'] = {'published': lastMessage['published'],
                                                 'content': lastMessage['object']['content']
                                                 }
        conversation['object']['messages'] = len(messages)

    handler = JSONResourceRoot(conversations)
    return handler.buildResponse()


@view_config(route_name='conversations', request_method='POST')
@MaxResponse
@MaxRequest
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

    # Initialize a conversation (context) object from the request, overriding the object using the context
    conversation_params = dict(actor=request.actor,
                               object=ctxts[0],
                               permissions={'read': 'subscribed',
                                            'write': 'subscribed',
                                            'join': 'restricted',
                                            'invite': 'restricted'},
                               hash=Conversation(ctxts[0]).getHash()
                               )
    newconversation = Context(request)
    newconversation.fromRequest(request, rest_params=conversation_params)

    if not request.actor.username in newconversation.object['participants']:
        raise ValidationError('Actor must be part of the participants list.')

    if not newconversation.get('_id'):
        # New conversation
        contextid = newconversation.insert()
        newconversation['_id'] = contextid

        # Subscribe everyone,
        for user in newconversation['object']['participants']:
            users[user].addSubscription(newconversation)
    else:
        # Subscriure users in participants conditionally
        subs_usernames = [user['username'] for user in newconversation.subscribedUsers()]
        unsubscribed = set(newconversation['object']['participants']).difference(set(subs_usernames))
        for user in unsubscribed:
            users[user].addSubscription(newconversation)

    # We have to re-get the actor, in order to have the subscription updated
    message_params = {'actor': users[request.actor['username']],
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
@MaxRequest
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
    messages = mmdb.activity.search(query, sort="published", sort_dir=ASCENDING, flatten=1)

    handler = JSONResourceRoot(messages)
    return handler.buildResponse()


@view_config(route_name='messages', request_method='POST')
@MaxResponse
@MaxRequest
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


