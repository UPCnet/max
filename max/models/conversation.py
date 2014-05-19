# -*- coding: utf-8 -*-
from max.models.context import BaseContext


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

    def realDisplayName(self, requester):
        """
            In two people conversations, force displayName to the displayName of
            the partner in the conversation, based on who's requesting conversation information
        """

        if 'group' not in self.get('tags', []):
            partner = [user for user in self['participants'] if user["username"] != requester.username][0]
            return partner["displayName"]
