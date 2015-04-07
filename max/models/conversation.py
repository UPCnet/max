# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.models.context import BaseContext
from max.rabbitmq import RabbitNotifications
from max.security import Manager
from max.security import Owner
from max.security import is_self_operation
from max.security.permissions import add_conversation_participant
from max.security.permissions import add_message
from max.security.permissions import delete_conversation
from max.security.permissions import delete_conversation_participant
from max.security.permissions import list_messages
from max.security.permissions import modify_conversation
from max.security.permissions import purge_conversations
from max.security.permissions import transfer_ownership
from max.security.permissions import view_conversation
from max.security.permissions import view_conversation_subscription
from max.utils.dicts import flatten

from pyramid.decorator import reify
from pyramid.security import Allow


class Conversation(BaseContext):
    """
        A conversation between people. This are normal contexts but stored in
        another collection
    """
    default_field_view_permission = view_conversation
    default_field_edit_permission = modify_conversation
    updatable_fields = ['permissions', 'displayName', 'tags', 'participants']
    collection = 'conversations'
    unique = '_id'
    user_subscription_storage = 'talkingIn'
    activity_storage = 'messages'
    schema = dict(BaseContext.schema)
    schema['participants'] = {'required': 1}
    schema['tags'] = {'default': []}
    schema['objectType'] = {'default': 'conversation'}

    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, view_conversation),
            (Allow, Manager, view_conversation_subscription),
            (Allow, Manager, modify_conversation),
            (Allow, Manager, delete_conversation),
            (Allow, Manager, purge_conversations),
            (Allow, Manager, add_conversation_participant),
            (Allow, Manager, delete_conversation_participant),
            (Allow, Manager, list_messages),
            (Allow, Manager, add_message),

            (Allow, Owner, view_conversation),
            (Allow, Owner, view_conversation_subscription),
            (Allow, Owner, modify_conversation),
            (Allow, Owner, delete_conversation),
        ]

        if self.subscription:
            acl.extend([
                (Allow, Manager, transfer_ownership),
                (Allow, Owner, transfer_ownership),
            ])
        # Grant extra permissions mapped to the authenticated user's
        # defined conversation subscription permissions

        subscription = self.request.creator.getSubscription(self)
        if subscription:
            # Allow user to view only its own subscription
            if is_self_operation(self.request):
                acl.append((Allow, self.request.authenticated_userid, view_conversation_subscription))

            if 'read' in subscription.get('permissions', []):
                acl.append((Allow, self.request.authenticated_userid, view_conversation))
                acl.append((Allow, self.request.authenticated_userid, list_messages))

            if 'write' in subscription.get('permissions', []) and is_self_operation(self.request):
                acl.append((Allow, self.request.authenticated_userid, add_message))

            if 'unsubscribe' in subscription.get('permissions', []) and is_self_operation(self.request):
                acl.append((Allow, self.request.authenticated_userid, delete_conversation_participant))

            if 'invite' in subscription.get('permissions', []):
                acl.append((Allow, self.request.authenticated_userid, add_conversation_participant))

            if 'kick' in subscription.get('permissions', []) and not is_self_operation(self.request):
                acl.append((Allow, self.request.authenticated_userid, delete_conversation_participant))

        return acl

    def buildObject(self):
        super(Conversation, self).buildObject()

        # Set displayName only if it's not specified
        self['displayName'] = self.get('displayName', ', '.join([a['username'] for a in self.participants]))

    def prepareUserSubscription(self):
        """
        """
        fields_to_squash = ['published', 'owner', 'creator', 'participants', 'tags', 'displayName']
        if '_id' != self.unique:
            fields_to_squash.append('_id')
        subscription = flatten(self, squash=fields_to_squash)

        # If we are subscribing the user, read permission is granted
        user_permissions = ['read']

        # Add subscription permissions based on defaults and context values
        user_permissions = self.subscription_permissions(base=user_permissions)

        # Assign permissions to the subscription object before adding it
        subscription['permissions'] = user_permissions
        return subscription

    def lastMessage(self):
        """
            Retrieves last conversation message
        """
        query = {
            'objectType': 'message',
            'contexts.id': self.getIdentifier()
        }

        message = MADMaxCollection(self.request, 'messages').last(query, flatten=True)

        lastMessage = {
            'published': message['published'],
            'content': message['object'].get('content', ''),
            'objectType': message['object']['objectType']
        }

        # Set object urls for media types
        if message['object']['objectType'] in ['file', 'image']:
            lastMessage['fullURL'] = message['object'].get('fullURL', '')
            if message['object']['objectType'] == 'image':
                lastMessage['thumbURL'] = message['object'].get('thumbURL', '')

        return lastMessage

    def getInfo(self, username):
        """
            Get conversation information, with proper adjustments
            to show the correct displayName and lasMessage settings
        """
        # make a copy to work with as the changes we'll made won't be stored
        conversation = self.flatten(keep_private_fields=True)
        conversation['displayName'] = self.realDisplayName(username)

        # DEPRECATED , Check if the apps/widget rely on this anymore
        conversation['messages'] = 0
        conversation['lastMessage'] = self.lastMessage()
        return conversation

    def realDisplayName(self, username):
        """
            In two people conversations, force displayName to the displayName of
            the partner in the conversation, based on who's requesting conversation information
        """
        if 'group' not in self.get('tags', []):
            partner = [user for user in self['participants'] if user["username"] != username][0]
            return partner["displayName"]
        else:
            return self['displayName']

    def _after_subscription_add(self, username):
        """
            Creates rabbitmq bindings after new subscription
        """
        notifier = RabbitNotifications(self.request)
        notifier.bind_user_to_conversation(self, username)

    def _after_subscription_remove(self, username):
        """
            Removes rabbitmq bindings after new subscription
        """
        notifier = RabbitNotifications(self.request)
        notifier.unbind_user_from_conversation(self, username)

    def _before_delete(self):
        self.removeUserSubscriptions()
        self.removeActivities(logical=False)

    def _after_delete(self):
        notifier = RabbitNotifications(self.request)
        notifier.unbind_conversation(self)
