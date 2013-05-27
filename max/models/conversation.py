# -*- coding: utf-8 -*-
from max.MADObjects import MADBase
from max.models.context import BaseContext
from max.rest.utils import getUserIdFromTwitter


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

        # If creating with the twitterUsername, get its Twitter ID
        if self.data.get('twitterUsername', None):
            self['twitterUsernameId'] = getUserIdFromTwitter(self.data['twitterUsername'])

        #Set displayName only if it's not specified
        self['displayName'] = self.get('displayName', ', '.join(self.participants))
