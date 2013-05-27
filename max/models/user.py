# -*- coding: utf-8 -*-
from max.MADObjects import MADBase
import datetime
from max.rest.utils import getMaxModelByObjectType


class User(MADBase):
    """
        An activitystrea.ms User object representation
    """
    collection = 'users'
    unique = 'username'
    schema = {'_id':          dict(),
              '_creator':     dict(required=0),
              '_owner':       dict(required=0),
              'objectType':   dict(required=0, default='person'),
              'username':     dict(required=1),
              'displayName':  dict(user_mutable=1),
              'last_login':   dict(),
              'following':    dict(default={'items': [], 'totalItems': 0}),
              'subscribedTo': dict(default={'items': [], 'totalItems': 0}),
              'talkingIn':    dict(default={'items': [], 'totalItems': 0}),
              'published':    dict(),
              'twitterUsername':    dict(user_mutable=1,
                                         formatters=['stripTwitterUsername'],
                                         validators=['isValidTwitterUsername']
                                         )
              }

    def buildObject(self):
        """
            Updates the dict content with the user structure,
            with data from the request
        """
        ob = {'last_login': datetime.datetime.utcnow()}

        # Update properties from request data if defined in schema
        # Also create properties with a default value defined
        properties = {}
        for key, value in self.schema.items():
            default = value.get('default', None)
            if key in self.data:
                properties[key] = self.data[key]
            elif 'default' in value.keys():
                properties[key] = default

        ob.update(properties)
        ob['displayName'] = ob.get('displayName', ob.get('username', 'nobody'))
        self.update(ob)

    def addFollower(self, person):
        """
            Adds a follower to the list
        """
        self.addToList('following', person)

    def addSubscription(self, context):
        """
            Adds a comment to an existing activity
        """
        subscription = context.prepareUserSubscription()
        self.addToList(context.user_subscription_storage, subscription, safe=False)

    def removeSubscription(self, context):
        """
            Adds a comment to an existing activity
        """
        self.deleteFromList(context.user_subscription_storage, {context.unique.lstrip('_'): context.getIdentifier()})

    def modifyUser(self, properties):
        """Update the user object with the given properties"""

        self.updateFields(properties)
        self.save()

    def grantPermission(self, subscription, permission):
        """
        """
        criteria = {}
        criteria.update({'subscribedTo.items.hash': subscription['hash']})   # update object from "items" that matches hash
        criteria.update({'_id': self._id})                 # of collection entry with _id

         # Add permission to permissions array, of matched object of "items"
        what = {'$addToSet': {'subscribedTo.items.$.permissions': permission}}

        self.mdb_collection.update(criteria, what)

    def revokePermission(self, subscription, permission):
        """
        """
        criteria = {}
        criteria.update({'subscribedTo.items.hash': subscription['hash']})   # update object from "items" that matches hash
        criteria.update({'_id': self._id})                 # of collection entry with _id

         # deletes permission from permissions array, of matched object of "items"
        what = {'$pull': {'subscribedTo.items.$.permissions': permission}}

        self.mdb_collection.update(criteria, what)

    def getSubscription(self, context):
        """
        """
        ContextClass = getMaxModelByObjectType(context['objectType'])
        temp_context = ContextClass()
        temp_context.fromObject(context)
        for subscription in self[temp_context.user_subscription_storage]['items']:
            if subscription[temp_context.unique.lstrip('_')] == temp_context[temp_context.unique]:
                return subscription
