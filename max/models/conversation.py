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
    schema['participants'] = dict(required=1)
    schema['objectType'] = dict(default='conversation')

    def buildObject(self):
        super(Conversation, self).buildObject()

        #Set displayName only if it's not specified
        self['displayName'] = self.get('displayName', ', '.join([a['username'] for a in self.participants]))
