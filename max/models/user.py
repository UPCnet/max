# -*- coding: utf-8 -*-
from max.MADObjects import MADBase
import datetime
from max.rest.utils import getMaxModelByObjectType, flatten

PLATFORM_FIELD_SUFFIX = 'Devices'


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
              'following':    dict(default=[]),
              'subscribedTo': dict(default=[]),
              'talkingIn':    dict(default=[]),
              'published':    dict(),
              'twitterUsername':    dict(user_mutable=1,
                                         formatters=['stripTwitterUsername'],
                                         validators=['isValidTwitterUsername']
                                         ),
              'iosDevices':     dict(default=[]),
              'androidDevices': dict(default=[]),
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
        self.add_to_list('following', person)

    def addSubscription(self, context):
        """
            Adds a comment to an existing activity
        """
        subscription = context.prepareUserSubscription()
        self.add_to_list(context.user_subscription_storage, subscription, safe=False)

    def removeSubscription(self, context):
        """
            Adds a comment to an existing activity
        """
        self.delete_from_list(context.user_subscription_storage, {context.unique.lstrip('_'): context.getIdentifier()})

    def modifyUser(self, properties):
        """Update the user object with the given properties"""

        self.updateFields(properties)
        self.save()

    def reset_permissions(self, subscription, context):

        subscription['_grants'] = []
        subscription['_vetos'] = []
        subscription['permissions'] = context.subscription_permissions()

        criteria = {}
        criteria.update({'subscribedTo.hash': subscription['hash']})   # update object that matches hash
        criteria.update({'_id': self._id})                 # of collection entry with _id

        # overwrite permissions
        what = {
            '$set': {
                'subscribedTo.$.permissions': subscription['permissions'],
                'subscribedTo.$._grants': subscription['_grants'],
                'subscribedTo.$._vetos': subscription['_vetos'],
            }
        }

        self.mdb_collection.update(criteria, what)

        fields_to_squash = ['published', 'owner', 'creator', 'tags', 'vetos', 'grants']
        subscription = flatten(subscription, squash=fields_to_squash)
        return subscription

    def grantPermission(self, subscription, permission):
        """
        Grant a permission persistently, so a change in the context permissions defaults doesn't
        leave the user without the permission
        """
        criteria = {}

        # Add current permissions
        new_permissions = list(subscription['permissions'])

        # Add new permission if not present
        if permission not in new_permissions:
            new_permissions.append(permission)

        # Add permission to grants if not present
        subscription.setdefault('_grants', [])
        if permission not in subscription['_grants']:
            subscription['_grants'].append(permission)

        # Remove permission from vetos if present
        subscription.setdefault('_vetos', [])
        subscription['_vetos'] = [vetted for vetted in subscription['_vetos'] if vetted != permission]

        criteria.update({'subscribedTo.hash': subscription['hash']})   # update object that matches hash
        criteria.update({'_id': self._id})                 # of collection entry with _id

         # overwrite permissions
        what = {
            '$set': {
                'subscribedTo.$.permissions': new_permissions,
                'subscribedTo.$._grants': subscription['_grants'],
                'subscribedTo.$._vetos': subscription['_vetos'],
            }
        }

        self.mdb_collection.update(criteria, what)

        # update subscription permissions
        subscription['permissions'] = new_permissions
        fields_to_squash = ['published', 'owner', 'creator', 'tags', 'vetos', 'grants']
        subscription = flatten(subscription, squash=fields_to_squash)

        return subscription

    def revokePermission(self, subscription, permission):
        """
        Revoke a permission persistently, so a change in the context permissions defaults doesn't
        grant the permission automatically
        """
        criteria = {}
        new_permissions = []

        # Add current permissions except revoked one
        new_permissions = [p for p in subscription['permissions'] if permission != p]

        # Add permission to vetos if not present
        subscription.setdefault('_vetos', [])
        if permission not in subscription['_vetos']:
            subscription['_vetos'].append(permission)

        # Remove permission from grants if present
        subscription.setdefault('_grants', [])
        subscription['_grants'] = [granted for granted in subscription['_grants'] if granted != permission]

        criteria.update({'subscribedTo.hash': subscription['hash']})   # update object that matches hash
        criteria.update({'_id': self._id})                 # of collection entry with _id

         # overwrite permissions
        what = {
            '$set': {
                'subscribedTo.$.permissions': new_permissions,
                'subscribedTo.$._grants': subscription['_grants'],
                'subscribedTo.$._vetos': subscription['_vetos'],
            }
        }
        subscription['permissions'] = new_permissions
        fields_to_squash = ['published', 'owner', 'creator', 'tags', 'vetos', 'grants']
        subscription = flatten(subscription, squash=fields_to_squash)

        self.mdb_collection.update(criteria, what)
        return subscription

    def getSubscription(self, context):
        """
        """
        ContextClass = getMaxModelByObjectType(context['objectType'])
        temp_context = ContextClass()
        temp_context.fromObject(context)
        for subscription in self[temp_context.user_subscription_storage]:
            if subscription[temp_context.unique.lstrip('_')] == temp_context[temp_context.unique]:
                return subscription

    def addUserDevice(self, platform, token):
        self.add_to_list(platform + PLATFORM_FIELD_SUFFIX, token)

    def deleteUserDevice(self, platform, token):
        self.delete_from_list(platform + PLATFORM_FIELD_SUFFIX, token)
