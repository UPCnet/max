# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent
from pymongo import ASCENDING

from max.exceptions import ValidationError, Unauthorized, Forbidden, ObjectNotFound
from max.MADMax import MADMaxDB, MADMaxCollection
from max.models import Message, Conversation, Activity
from max.decorators import MaxResponse, requirePersonActor
from max.oauth2 import oauth2
from max import DEFAULT_CONTEXT_PERMISSIONS
from max import CONVERSATION_PARTICIPANTS_LIMIT
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.rest.utils import extractPostData
from max.rabbitmq.notifications import messageNotification
from max.rabbitmq.notifications import addConversationExchange


@view_config(route_name='conversations', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getConversations(context, request):
    """
         /conversations
         Return all conversations depending on the actor requester
    """
    mmdb = MADMaxDB(context.db)
    query = {'participants': request.actor['username'],
             'objectType': 'conversation',
             }

    conversations = mmdb.conversations.search(query, sort="published", flatten=1, keep_private_fields=True)
    for conversation in conversations:
        query = {'objectType': 'message',
                 'contexts.id': conversation['id']
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
@oauth2(['widgetcli'])
@requirePersonActor
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
    if len(ctxts[0].get('participants', [])) == 0:
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
        participants_query = [
            {'participants': {'$in': [ctxts[0]['participants'][0], ]}},
            {'participants': {'$in': [ctxts[0]['participants'][1], ]}},
        ]
        conversations = contexts.search({'objectType': 'conversation', '$and': participants_query})
        conversations = [a for a in conversations if len(a.participants) == 2]
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
        newconversation = Conversation()
        newconversation.fromRequest(request, rest_params=conversation_params)

        if not request.actor.username in newconversation['participants']:
            raise ValidationError('Actor must be part of the participants list.')

        # New conversation
        contextid = newconversation.insert()
        newconversation['_id'] = contextid

        # Subscribe everyone,
        for user in newconversation['participants']:
            db_user = users[user]
            db_user.addSubscription(newconversation)
            # Initialize a Subscription Activity
            rest_params = {'actor': db_user,
                           'verb': 'subscribe',
                           'object': {'objectType': 'conversation',
                                      'id': newconversation['_id'],
                                      'participants': newconversation.participants},
                           'contexts': []  # Override contexts from request

                           }
            newactivity = Activity()
            newactivity.fromRequest(request, rest_params=rest_params)
            newactivity_oid = newactivity.insert()  # Insert a subscribe activity
            newactivity['_id'] = newactivity_oid

        current_conversation = newconversation

    # We have to re-get the actor, in order to have the subscription updated
    message_params = {'actor': users[request.actor['username']],
                      'contexts': [{'objectType': 'conversation',
                                    'id': current_conversation.getIdentifier()
                                    }],
                      'verb': 'post'}

    # Initialize a Message (Activity) object from the request
    newmessage = Message()
    try:
        newmessage.fromRequest(request, rest_params=message_params)
    except Exception as Catched:
        # In case we coulnd't post the message, rollback conversation and subscriptions
        current_conversation.removeUserSubscriptions()
        current_conversation.delete()
        raise Catched

    message_oid = newmessage.insert()
    newmessage['_id'] = message_oid

    addConversationExchange(current_conversation)
    messageNotification(newmessage)

    handler = JSONResourceEntity(newmessage.flatten(), status_code=201)
    return handler.buildResponse()


@view_config(route_name='messages', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getMessages(context, request):
    """
         /conversations/{id}/messages
         Return all messages from a conversation
    """
    cid = request.matchdict['id']
    if cid not in [ctxt.get("id", '') for ctxt in request.actor.talkingIn]:
        raise Unauthorized('User {} is not allowed to view this conversation'.format(request.actor.username))

    mmdb = MADMaxDB(context.db)
    query = {'contexts.id': cid}
    messages = mmdb.messages.search(query, sort="published", sort_dir=ASCENDING, flatten=1, keep_private_fields=False)

    handler = JSONResourceRoot(messages)
    return handler.buildResponse()


@view_config(route_name='conversation', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getConversation(context, request):
    """
         /conversations/{id}
         Return Conversation
    """
    cid = request.matchdict['id']
    conversations = MADMaxCollection(context.db.conversations)
    conversation = conversations[cid]

    if cid not in [ctxt.get("id", '') for ctxt in request.actor.talkingIn]:
        raise Unauthorized('User {} is not allowed to view this conversation'.format(request.actor.username))

    if len(conversation.participants) == 2:
        participants = list(conversation.participants)
        participants.remove(request.actor.username)
        users = MADMaxCollection(context.db.users, query_key='username')
        partner = users[participants[0]]
        conversation.displayName = partner.displayName

    handler = JSONResourceEntity(conversation.flatten())
    return handler.buildResponse()


@view_config(route_name='conversation', request_method='PUT')
@MaxResponse
@oauth2(['widgetcli'])
def ModifyContext(context, request):
    """
        /conversation/{id}

        Modify the given context.
    """
    cid = request.matchdict['id']
    conversations = MADMaxCollection(context.db.conversations)
    conversation = conversations[cid]

    auth_user_is_conversation_owner = conversation._owner == request.creator

    if not auth_user_is_conversation_owner:
        raise Unauthorized('Only the owner modify conversation properties')

    properties = conversation.getMutablePropertiesFromRequest(request)
    conversation.modifyContext(properties)
    conversation.updateUsersSubscriptions()
    handler = JSONResourceEntity(conversation.flatten())
    return handler.buildResponse()


@view_config(route_name='messages', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def addMessage(context, request):
    """
         /conversations/{id}/messages
         Post a message to 1 (one) existing conversation
    """
    cid = request.matchdict['id']
    message_params = {'actor': request.actor,
                      'verb': 'post',
                      'contexts': [{'objectType': 'conversation',
                                    'id': cid
                                    }]
                      }

    # Initialize a Message (Activity) object from the request
    newmessage = Message()
    newmessage.fromRequest(request, rest_params=message_params)

    message_oid = newmessage.insert()
    newmessage['_id'] = message_oid

    messageNotification(newmessage)

    handler = JSONResourceEntity(newmessage.flatten(), status_code=201)
    return handler.buildResponse()


@view_config(route_name='user_conversation', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def joinConversation(context, request):
    """
         /people/{username}/conversations/{id}/participants
         Adds a participant to a conversation
    """
    actor = request.actor
    cid = request.matchdict['id']

    #Check if user is already subscribed
    current_conversations = [a['id'] for a in actor.talkingIn]
    if cid in current_conversations:
        # If user already subscribed, send a 200 code and retrieve the original subscribe activity
        # post when user was susbcribed. This way in th return data we'll have the date of subscription
        code = 200
        activities = MADMaxCollection(context.db.activity)
        query = {'verb': 'subscribe', 'object.id': cid, 'actor.username': actor.username}
        newactivity = activities.search(query)[-1]  # Pick the last one, so we get the last time user subscribed (in cas a unsbuscription occured sometime...)

    else:
        #Register subscription to the actor
        conversations = MADMaxCollection(context.db.conversations)
        conversation = conversations[cid]

        if len(conversation.participants) == CONVERSATION_PARTICIPANTS_LIMIT:
            raise Forbidden('This conversation is full, no more of {} participants allowed'.format(CONVERSATION_PARTICIPANTS_LIMIT))

        # The owner of the conversation must be the same as the request creator to subscribe people to restricted conversations
        if conversation.permissions.get('subscribe', DEFAULT_CONTEXT_PERMISSIONS['subscribe']) == 'restricted' and \
                conversation._owner != request.creator:

            raise Unauthorized('User {0} cannot subscribe himself to to this context'.format(actor['username']))

        actor.addSubscription(conversation)
        conversation.participants.append(actor.username)
        conversation.save()

        # If user wasn't created, 201 will show that the subscription has just been added
        code = 201

        # Initialize a Activity object from the request
        rest_params = {'actor': actor,
                       'verb': 'subscribe',
                       'object': {'objectType': 'conversation',
                                  'id': cid,
                                  'participants': conversation.participants}
                       }

        newactivity = Activity()
        newactivity.fromRequest(request, rest_params=rest_params)
        newactivity_oid = newactivity.insert()  # Insert a subscribe activity
        newactivity['_id'] = newactivity_oid
    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='user_conversation', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def leaveConversation(context, request):
    """
    """
    actor = request.actor
    mmdb = MADMaxDB(context.db)
    cid = request.matchdict.get('id', None)
    subscription = actor.getSubscription({'id': cid, 'objectType': 'conversation'})

    if subscription is None:
        raise ObjectNotFound("User {0} is not in conversation {1}".format(actor.username, cid))

    found_context = mmdb.conversations[cid]

    auth_user_is_conversation_owner = found_context._owner == request.creator
    auth_user_is_leaving = request.creator == actor.username

    if auth_user_is_conversation_owner and auth_user_is_leaving:
        raise Forbidden('User {0} is the owner of the conversation, leaving is not allowed, only deleting'.format(actor.username))

    if not auth_user_is_leaving and not auth_user_is_conversation_owner:
        raise Unauthorized('Only conversation owner can force participants out')

    actor.removeSubscription(found_context)
    found_context.participants.remove(actor.username)
    found_context.save()
    return HTTPNoContent()


@view_config(route_name='conversation', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
def DeleteConversation(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    cid = request.matchdict.get('id', None)
    ctx = mmdb.conversations[cid]

    auth_user_is_conversation_owner = ctx._owner == request.creator

    if not auth_user_is_conversation_owner:
        raise Unauthorized('Only the owner can delete the conversation')

    ctx.removeUserSubscriptions()
    ctx.removeActivities(logical=False)
    ctx.delete()
    return HTTPNoContent()
