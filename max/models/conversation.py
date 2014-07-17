# -*- coding: utf-8 -*-
from max.models.context import BaseContext
from max.MADMax import MADMaxCollection
from pymongo import DESCENDING
from max.rabbitmq import RabbitNotifications


class Conversation(BaseContext):
    """
        A conversation between people. This are normal contexts but stored in
        another collection
    """
    collection = 'conversations'
    unique = '_id'
    user_subscription_storage = 'talkingIn'
    activity_storage = 'messages'
    schema = dict(BaseContext.schema)
    schema['participants'] = {'required': 1}
    schema['tags'] = {'default': []}
    schema['objectType'] = {'default': 'conversation'}

    def buildObject(self):
        super(Conversation, self).buildObject()

        #Set displayName only if it's not specified
        self['displayName'] = self.get('displayName', ', '.join([a['username'] for a in self.participants]))

    def lastMessage(self):
        """
            Retrieves last conversation message
        """
        query = {
            'objectType': 'message',
            'contexts.id': self.getIdentifier()
        }

        messages = MADMaxCollection(self.db.messages).search(query, flatten=1, limit=1, sort="published", sort_dir=DESCENDING)
        message = messages[0]
        lastMessage = {
            'published': message['published'],
            'content': message['object'].get('content', ''),
            'objectType': message['object']['objectType']
        }

        #Set object urls for media types
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
