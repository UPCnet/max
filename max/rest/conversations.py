# -*- coding: utf-8 -*-
from max import CONVERSATION_PARTICIPANTS_LIMIT
from max import DEFAULT_CONTEXT_PERMISSIONS
from max.MADMax import MADMaxCollection
from max.MADMax import MADMaxDB
from max.decorators import MaxResponse
from max.decorators import requirePersonActor
from max.exceptions import Forbidden
from max.exceptions import ObjectNotFound
from max.exceptions import Unauthorized
from max.exceptions import ValidationError
from max.models import Activity
from max.models import Conversation
from max.models import Message
from max.oauth2 import oauth2
from max.rabbitmq import RabbitNotifications
from max.rest.ResourceHandlers import JSONResourceEntity
from max.rest.ResourceHandlers import JSONResourceRoot
from max.rest.utils import extractPostData
from max.rest.utils import flatten
from max.rest.utils import searchParams

from pyramid.httpexceptions import HTTPNoContent
from pyramid.response import Response
from pyramid.view import view_config

from bson import ObjectId
from pymongo import DESCENDING

import os


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

    # List subscribed conversations, and use it to make the query
    # This way we can filter 2-people conversations that have been archived
    subscribed_conversations = [ObjectId(subscription.get('id')) for subscription in request.actor.get('talkingIn', [])]

    query = {'participants.username': request.actor['username'],
             'objectType': 'conversation',
             '_id': {'$in': subscribed_conversations}
             }

    conversations = mmdb.conversations.search(query, sort_by_field="published")

    conversations_info = []
    for conversation in conversations:

        conversation_info = conversation.getInfo(request.actor.username)
        conversations_info.append(conversation_info)

    sorted_conversations = sorted(conversations_info, reverse=True, key=lambda conv: conv['lastMessage']['published'])

    handler = JSONResourceRoot(sorted_conversations)
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

    request_participants = ctxts[0].get('participants', [])
    if len(request_participants) == 0:
        raise ValidationError('Empty participants parameter')
    if len(request_participants) != len(list(set(request_participants))):
        raise ValidationError('One or more users duplicated in participants list')
    if len(request_participants) == 1 and request_participants[0] == request.actor.username:
        raise ValidationError('Cannot start a convesation with oneself')

    if request.actor.username not in request_participants:
        raise ValidationError('Actor must be part of the participants list.')

    # Loop trough all participants, if there's one that doesn't exists, an exception will raise
    # This check is to avoid any conversation creation if there's any invalid participant
    # Also store the definitive list that will be saved in participants field

    participants = {}
    users = MADMaxCollection(context.db.users, query_key='username')
    for participant in request_participants:
        user = users[participant]
        if request.actor.username != user['username'] and not request.actor.isAllowedToSee(user):
            raise Unauthorized('User {} is not allowed to have a conversation with {}'.format(request.actor.username, user['username']))
        participants[participant] = user

    # If there are only two participants in the conversation, try to get an existing conversation
    # Otherwise, assume is a group conversation and create a new one
    current_conversation = None
    if len(request_participants) == 2:
        contexts = MADMaxCollection(context.db.conversations)
        conversations = contexts.search({
            'objectType': 'conversation',
            'participants': {
                '$size': 2},
            'tags': {'$not': {'$in': ['group']}},
            'participants.username': {
                '$all': request_participants}
        })

        if conversations:
            current_conversation = conversations[0]

    if current_conversation is None:
        # Initialize a conversation (context) object from the request, overriding the object using the context
        conversation_params = dict(actor=request.actor,
                                   tags=['group'] if len(participants) > 2 else [],
                                   participants=[participant.flatten(preserve=['displayName', 'objectType', 'username']) for participant in participants.values()],
                                   permissions={'read': 'subscribed',
                                                'write': 'subscribed',
                                                'subscribe': 'restricted',
                                                'unsubscribe': 'public',
                                                'invite': 'restricted'})
        if ctxts[0].get('displayName', False):
            conversation_params['displayName'] = ctxts[0]['displayName']
        newconversation = Conversation()
        newconversation.fromRequest(request, rest_params=conversation_params)

        # New conversation
        contextid = newconversation.insert()
        newconversation['_id'] = contextid

        # Subscribe everyone,
        for user in newconversation['participants']:
            db_user = participants[user['username']]
            db_user.addSubscription(newconversation)
            # Initialize a Subscription Activity
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
    updated_user = users[request.actor['username']]
    message_params = {'actor': updated_user,
                      'contexts': [{'objectType': 'conversation',
                                    'id': current_conversation.getIdentifier()
                                    }],
                      'verb': 'post'}

    # Initialize a Message (Activity) object from the request
    newmessage = Message()
    try:
        newmessage.fromRequest(request, rest_params=message_params)
    except Exception as Catched:
        # In case we coulnd't post the message, rollback conversation creation
        current_conversation.delete()
        raise Catched

    # Grant subscribe permission to the user creating the conversation, only if the conversation
    # is bigger than 2 people. Conversations that are created with only 2 people from the beggining
    # Will not be able to grow
    if len(current_conversation.participants) > 2:
        updated_user.grantPermission(updated_user.getSubscription(current_conversation), 'subscribe', permanent=True)

    message_oid = newmessage.insert()
    newmessage['_id'] = message_oid

    output_message = newmessage.flatten()
    output_message['contexts'][0]['displayName'] = current_conversation.realDisplayName(request.actor)
    output_message['contexts'][0]['tags'] = current_conversation.get('tags', [])

    # Notification is done here because we don't want to do it right after insertion
    # as a possible rollback would cause a  notification of a inexistent conversation
    notifier = RabbitNotifications(request)
    notifier.add_conversation(current_conversation)

    handler = JSONResourceEntity(output_message, status_code=201)
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
    messages = mmdb.messages.search(query, sort_by_field="published", keep_private_fields=False, **searchParams(request))
    remaining = messages.remaining
    handler = JSONResourceRoot(flatten(messages[::-1]), remaining=remaining)
    return handler.buildResponse()


@view_config(route_name='user_conversation', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getUserConversationSubscription(context, request):
    """
         /people/{username}/conversations/{id}
         Return Conversation subscription
    """
    if request.actor.username != request.creator:
        raise Unauthorized('User {} is not allowed to view this conversation subscription'.format(request.actor.username))

    cid = request.matchdict['id']
    if cid not in [ctxt.get("id", '') for ctxt in request.actor.talkingIn]:
        raise Unauthorized('User {} is not subscriped to any conversation with id {}'.format(request.actor.username, cid))

    subscription = request.actor.getSubscription({'id': cid, 'objectType': 'conversation'})

    conversations_collection = MADMaxCollection(context.db.conversations)
    conversation_object = conversations_collection[subscription['id']]
    conversation = conversation_object.flatten()

    # Update temporary conversation with subscription permissions and other stuff
    conversation['displayName'] = conversation_object.realDisplayName(request.actor.username)
    conversation['lastMessage'] = conversation_object.lastMessage()
    conversation['permissions'] = subscription['permissions']
    conversation['messages'] = 0

    handler = JSONResourceEntity(conversation)
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

    subscribed_conversations = [subscription.get('id') for subscription in request.actor.get('talkingIn', [])]

    if cid not in subscribed_conversations:
        raise Unauthorized("You're not a participant in this conversation")

    handler = JSONResourceEntity(conversation.getInfo(request.actor.username))
    return handler.buildResponse()


@view_config(route_name='conversation', request_method='PUT')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
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
    conversation.updateContextActivities()
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

    if newmessage['object']['objectType'] == u'image' or \
       newmessage['object']['objectType'] == u'file':
        # Extract the file before saving object
        message_file = newmessage.extract_file_from_activity()
        message_oid = newmessage.insert()
        newmessage['_id'] = ObjectId(message_oid)
        newmessage.process_file(request, message_file)
        newmessage.save()
    else:
        message_oid = newmessage.insert()
        newmessage['_id'] = message_oid

    handler = JSONResourceEntity(newmessage.flatten(), status_code=201)
    return handler.buildResponse()


@view_config(route_name='user_conversation', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def joinConversation(context, request):
    """
         /people/{username}/conversations/{id}
    """
    actor = request.actor
    cid = request.matchdict['id']

    # Check if user is already subscribed
    current_conversations = [a['id'] for a in actor.talkingIn]
    if cid in current_conversations:
        # If user already subscribed, send a 200 code and retrieve the original subscribe activity
        # post when user was subscribed. This way in th return data we'll have the date of subscription
        code = 200
        activities = MADMaxCollection(context.db.activity)
        query = {'verb': 'subscribe', 'object.id': cid, 'actor.username': actor.username}
        newactivity = activities.search(query)[-1]  # Pick the last one, so we get the last time user subscribed (in cas a unsbuscription occured sometime...)

    else:
        # Register subscription to the actor
        conversations = MADMaxCollection(context.db.conversations)
        conversation = conversations[cid]

        if len(conversation.participants) == CONVERSATION_PARTICIPANTS_LIMIT:
            raise Forbidden('This conversation is full, no more of {} participants allowed'.format(CONVERSATION_PARTICIPANTS_LIMIT))

        if 'group' not in conversation.get('tags', []):
            raise Forbidden('This is not a group conversation, so no one else is allowed'.format(CONVERSATION_PARTICIPANTS_LIMIT))

        users = MADMaxCollection(context.db.users, query_key='username')
        creator = users[request.creator]

        authenticated_user_is_owner = conversation._owner == request.creator
        only_owner_can_subscribe = conversation.permissions.get('subscribe', DEFAULT_CONTEXT_PERMISSIONS['subscribe']) == 'restricted'
        authenticated_user_can_subscribe = 'subscribe' in creator.getSubscription(conversation)['permissions']
        # The owner of the conversation must be the same as the request creator to subscribe people to restricted conversations

        if only_owner_can_subscribe and (not authenticated_user_is_owner or not authenticated_user_can_subscribe):
            raise Unauthorized('User {0} cannot subscribe people to this conversation'.format(actor['username']))

        if not creator.isAllowedToSee(actor):
            raise Unauthorized('User {} is not allowed to have a conversation with {}'.format(creator.username, actor.username))

        conversation.participants.append(actor.flatten(preserve=['displayName', 'objectType', 'username']))
        actor.addSubscription(conversation)

        # If we add anyone to a conversation,  we remove the archive tag, no matter how many participants have
        if 'archive' in conversation.get('tags', []):
            conversation.tags.remove('archive')

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


@view_config(route_name='conversation_owner', request_method='PUT')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def trasnferConversationOwnership(context, request):
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

    if not auth_user_is_conversation_owner:
        raise Unauthorized('Only conversation owner can transfer conversation ownership')

    # Check if the targeted new owner is on the conversation
    request.actor.getSubscription({'id': cid, 'objectType': 'conversation'})

    if subscription is None:
        raise ObjectNotFound("Cannot transfer ownership to {0}. User is not in conversation {1}".format(actor.username, cid))

    previous_owner_username = found_context._owner
    found_context._owner = request.actor.username
    found_context.save()

    # Give hability to add new users to the new owner
    request.actor.grantPermission(subscription, 'subscribe', permanent=True)

    # Revoke hability to add new users from the previous owner
    users = MADMaxCollection(context.db.users, query_key='username')
    previous_owner = users[previous_owner_username]
    previous_owner.revokePermission(subscription, 'subscribe')

    handler = JSONResourceEntity(found_context.flatten())
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

    # Unsubscribe leaving participant ALWAYS
    actor.removeSubscription(found_context)

    save_context = False
    # Remove leaving participant from participants list ONLY for group conversations of >=2 participants
    if len(found_context.participants) >= 2 and 'group' in found_context.get('tags', []):
        found_context.participants = [user for user in found_context.participants if user['username'] != actor.username]
        save_context = True

    # Tag conversations that will be left as 1 participant only as archived
    if len(found_context.participants) == 2:
        found_context.setdefault('tags', [])
        if 'archive' not in found_context['tags']:
            found_context['tags'].append('archive')
            save_context = True

    if save_context:
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

    ctx.delete()
    return HTTPNoContent()


@view_config(route_name='conversation_avatar', request_method='GET')
def getConversationUserAvatar(context, request):
    """
        /conversation/{id}/avatar

        Returns conversation avatar. Public endpoint.
    """
    AVATAR_FOLDER = request.registry.settings.get('avatar_folder')
    cid = request.matchdict['id']
    filename = cid if os.path.exists(os.path.join(AVATAR_FOLDER, '{}.png'.format(cid))) else 'missing-conversation'
    data = open(os.path.join(AVATAR_FOLDER, '{}.png'.format(filename))).read()
    image = Response(data, status_int=200)
    image.content_type = 'image/png'
    return image
