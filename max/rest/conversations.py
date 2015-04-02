# -*- coding: utf-8 -*-
from max import CONVERSATION_PARTICIPANTS_LIMIT
from max.MADMax import MADMaxCollection
from max.exceptions import Forbidden
from max.exceptions import ObjectNotFound
from max.exceptions import Unauthorized
from max.exceptions import ValidationError
from max.models import Activity
from max.models import Conversation
from max.models import Message
from max.rabbitmq import RabbitNotifications
from max.rest.ResourceHandlers import JSONResourceEntity
from max.rest.ResourceHandlers import JSONResourceRoot
from max.rest import endpoint
from max.security.permissions import add_conversation_for_others, list_conversations, add_conversation, view_conversation, view_conversation_subscription, modify_conversation, delete_conversation, purge_conversations, add_conversation_participant, delete_conversation_participant
from pyramid.httpexceptions import HTTPNoContent

from bson import ObjectId


@endpoint(route_name='conversations', request_method='GET', requires_actor=True, permission=list_conversations)
def getConversations(conversations, request):
    """
         /conversations
         Return all conversations owned by the requesting actor
    """
    # List subscribed conversations, and use it to make the query
    # This way we can filter 2-people conversations that have been archived
    subscribed_conversations = [ObjectId(subscription.get('id')) for subscription in request.actor.get('talkingIn', [])]

    query = {'participants.username': request.actor['username'],
             'objectType': 'conversation',
             '_id': {'$in': subscribed_conversations}
             }

    conversations_search = conversations.search(query, sort_by_field="published")

    conversations_info = []
    for conversation in conversations_search:

        conversation_info = conversation.getInfo(request.actor.username)
        conversations_info.append(conversation_info)

    sorted_conversations = sorted(conversations_info, reverse=True, key=lambda conv: conv['lastMessage']['published'])

    handler = JSONResourceRoot(sorted_conversations)
    return handler.buildResponse()


@endpoint(route_name='conversations', request_method='POST', requires_actor=True, permission=add_conversation)
def postMessage2Conversation(conversations, request):
    """
         /conversations
         Post message to a conversation
    """
    # We are forced the check and extract the context of the conversation here,
    # We can't initialize the activity first, because it would fail (chiken-egg stuff)
    data = request.decoded_payload
    ctxts = data.get('contexts', [])
    if len(ctxts) == 0:
        raise ValidationError('Empty contexts parameter')

    request_participants = ctxts[0].get('participants', [])
    if len(request_participants) == 0:
        raise ValidationError('Empty participants parameter')
    if len(request_participants) != len(list(set(request_participants))):
        raise ValidationError('One or more users duplicated in participants list')
    if len(request_participants) == 1 and request_participants[0] == request.actor.username:
        raise ValidationError('Cannot start a conversation with oneself')

    if request.actor.username not in request_participants and not request.has_permission(add_conversation_for_others):
        raise ValidationError('Actor must be part of the participants list.')

    # Loop trough all participants, if there's one that doesn't exists, an exception will raise
    # This check is to avoid any conversation creation if there's any invalid participant
    # Also store the definitive list that will be saved in participants field

    participants = {}
    users = MADMaxCollection(request.db.users, query_key='username')
    for participant in request_participants:
        user = users[participant]
        if request.actor.username != user['username'] and not request.actor.is_allowed_to_see(user):
            raise Forbidden('User {} is not allowed to have a conversation with {}'.format(request.actor.username, user['username']))
        participants[participant] = user

    # If there are only two participants in the conversation, try to get an existing conversation
    # Otherwise, assume is a group conversation and create a new one
    current_conversation = None
    if len(request_participants) == 2:
        conversations_search = conversations.search({
            'objectType': 'conversation',
            'participants': {
                '$size': 2},
            'tags': {'$not': {'$in': ['group']}},
            'participants.username': {
                '$all': request_participants}
        })

        if conversations_search:
            current_conversation = conversations_search[0]

    if current_conversation is None:
        # Initialize a conversation (context) object from the request, overriding the object using the context
        conversation_params = dict(actor=request.actor,
                                   tags=['group'] if len(participants) > 2 else [],
                                   participants=[participant.flatten(preserve=['displayName', 'objectType', 'username']) for participant in participants.values()],
                                   permissions={'read': 'subscribed',
                                                'write': 'subscribed',
                                                'subscribe': 'restricted',
                                                'unsubscribe': 'subscribed'})
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

    # We need to reload the actor, in order to have the subscription updated
    # We need to reload reified acl's, so then new actor subscription will be visible by __acl__
    request.actor.reload()
    current_conversation.reload__acl__()

    message_params = {'actor': request.actor,
                      'contexts': [current_conversation],
                      'verb': 'post'}

    # Initialize a Message (Activity) object from the request
    newmessage = Message()

    try:
        newmessage.fromRequest(request, rest_params=message_params)
    except Exception as catched:
        # In case we coulnd't post the message, rollback conversation creation
        current_conversation.delete()
        raise catched

    # Grant subscribe permission to the user creating the conversation, only if the conversation
    # is bigger than 2 people. Conversations that are created with only 2 people from the beggining
    # Will not be able to grow

    if len(current_conversation.participants) > 2:
        subscription = request.actor.getSubscription(current_conversation)
        request.actor.grantPermission(subscription, 'invite', permanent=False)
        request.actor.grantPermission(subscription, 'kick', permanent=False)
        request.actor.revokePermission(subscription, 'unsubscribe', permanent=False)

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


@endpoint(route_name='conversation', request_method='GET', requires_actor=True, permission=view_conversation)
def getConversation(conversation, request):
    """
         /conversations/{id}
         Return Conversation
    """
    handler = JSONResourceEntity(conversation.getInfo(request.actor.username))
    return handler.buildResponse()


@endpoint(route_name='user_conversation', request_method='GET', requires_actor=True, permission=view_conversation_subscription)
def getUserConversationSubscription(conversation, request):
    """
         /people/{username}/conversations/{id}
         Return Conversation subscription
    """
    subscription = conversation.subscription

    conversations_collection = conversation.__parent__
    conversation_object = conversations_collection[subscription['id']]
    conversation = conversation_object.flatten()

    # Update temporary conversation with subscription permissions and other stuff
    conversation['displayName'] = conversation_object.realDisplayName(request.actor.username)
    conversation['lastMessage'] = conversation_object.lastMessage()
    conversation['permissions'] = subscription['permissions']
    conversation['messages'] = 0

    handler = JSONResourceEntity(conversation)
    return handler.buildResponse()


@endpoint(route_name='conversation', request_method='PUT', requires_actor=True, permission=modify_conversation)
def ModifyConversation(conversation, request):
    """
        /conversation/{id}

        Modify the given context.
    """
    properties = conversation.getMutablePropertiesFromRequest(request)
    conversation.modifyContext(properties)
    conversation.updateUsersSubscriptions()
    conversation.updateContextActivities()
    handler = JSONResourceEntity(conversation.flatten())
    return handler.buildResponse()


@endpoint(route_name='conversation', request_method='DELETE', requires_actor=True, permission=delete_conversation)
def DeleteConversation(conversation, request):
    """
    """
    conversation.delete()
    return HTTPNoContent()


@endpoint(route_name='conversations', request_method='DELETE', requires_actor=True, permission=purge_conversations)
def deleteConversations(conversations, request):
    """
    Deletes ALL the conversations from ALL users in max
    doing all the consequent unsubscriptions
    """
    for conversation in conversations.dump():
        conversation.delete()
    return HTTPNoContent()


@endpoint(route_name='participants', request_method='POST', requires_actor=True, permission=add_conversation_participant)
def joinConversation(conversation, request):
    """

    """
    actor = request.actor
    cid = request.matchdict['id']

    # Check if user is already subscribed
    if conversation.subscription:
        # If user already subscribed, send a 200 code and retrieve the original subscribe activity
        # post when user was subscribed. This way in th return data we'll have the date of subscription
        code = 200
        activities = MADMaxCollection(request.db.activity)
        query = {'verb': 'subscribe', 'object.id': cid, 'actor.username': actor.username}
        newactivity = activities.search(query)[-1]  # Pick the last one, so we get the last time user subscribed (in cas a unsbuscription occured sometime...)

    else:
        if len(conversation.participants) == CONVERSATION_PARTICIPANTS_LIMIT:
            raise Forbidden('This conversation is full, no more of {} participants allowed'.format(CONVERSATION_PARTICIPANTS_LIMIT))

        if 'group' not in conversation.get('tags', []):
            raise Forbidden('This is not a group conversation, so no one else is allowed'.format(CONVERSATION_PARTICIPANTS_LIMIT))

        if not request.creator.is_allowed_to_see(actor):
            raise Unauthorized('User {} is not allowed to have a conversation with {}'.format(request.creator.username, actor.username))

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


@endpoint(route_name='participant', request_method='DELETE', requires_actor=True, permission=delete_conversation_participant)
def leaveConversation(conversation, request):
    """
    """
    actor = request.actor

    # Unsubscribe leaving participant ALWAYS
    actor.removeSubscription(conversation)

    save_context = False
    # Remove leaving participant from participants list ONLY for group conversations of >=2 participants
    if len(conversation.participants) >= 2 and 'group' in conversation.get('tags', []):
        conversation.participants = [user for user in conversation.participants if user['username'] != actor.username]
        save_context = True

    # Tag conversations that will be left as 1 participant only as archived
    if len(conversation.participants) == 2:
        conversation.setdefault('tags', [])
        if 'archive' not in conversation['tags']:
            conversation['tags'].append('archive')
            save_context = True

    if save_context:
        conversation.save()

    return HTTPNoContent()


@endpoint(route_name='conversation_owner', request_method='PUT', requires_actor=True, permission=modify_conversation)
def transferConversationOwnership(conversation, request):
    """
    """
    actor = request.actor
    cid = request.matchdict.get('id', None)
    subscription = conversation.subscription

    # Check if the targeted new owner is on the conversation
    request.actor.getSubscription({'id': cid, 'objectType': 'conversation'})

    if subscription is None:
        raise ObjectNotFound("Cannot transfer ownership to {0}. User is not in conversation {1}".format(actor.username, cid))

    previous_owner_username = conversation._owner
    conversation._owner = request.actor.username
    conversation.save()

    # Give hability to add new users to the new owner
    request.actor.grantPermission(subscription, 'invite', permanent=True)
    request.actor.grantPermission(subscription, 'kick', permanent=True)
    request.actor.revokePermission(subscription, 'unsubscribe', permanent=True)

    # Revoke hability to add new users from the previous owner
    users = MADMaxCollection(request.db.users, query_key='username')
    previous_owner = users[previous_owner_username]
    previous_owner.revokePermission(subscription, 'invite')
    previous_owner.revokePermission(subscription, 'kick')
    previous_owner.grantPermission(subscription, 'unsubscribe')

    handler = JSONResourceEntity(conversation.flatten())
    return handler.buildResponse()
