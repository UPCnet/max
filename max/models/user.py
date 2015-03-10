# -*- coding: utf-8 -*-
from max import DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY
from max.MADObjects import MADBase
from max.MADMax import MADMaxCollection
from max.rabbitmq import RabbitNotifications
from max.rest.utils import flatten
from max.rest.utils import getMaxModelByObjectType

from bson import ObjectId
from pyramid.settings import asbool

import datetime


PLATFORM_FIELD_SUFFIX = 'Devices'


class User(MADBase):
    """
        An activitystrea.ms User object representation
    """
    default_field_view_roles = ['Owner', 'Manager']
    collection = 'users'
    unique = 'username'
    schema = {
        '_id': {},
        '_creator': {},
        '_owner': {},
        'objectType': {
            'default': 'person'
        },
        'username': {
            'required': 1,
            'view': ['Owner', 'Manager', 'Authenticated']
        },
        'displayName': {
            'edit': ['Owner', 'Manager'],
            'view': ['Owner', 'Manager', 'Authenticated']
        },
        'last_login': {},
        'following': {
            'default': []
        },
        'subscribedTo': {
            'default': []
        },
        'talkingIn': {
            'default': []
        },
        'published': {},
        'twitterUsername': {
            'edit': ['Owner', 'Manager'],
            'view': ['Owner', 'Manager', 'Authenticated'],
            'formatters': ['stripTwitterUsername'],
            'validators': ['isValidTwitterUsername']
        },
        'iosDevices': {
            'default': []
        },
        'androidDevices': {
            'default': []
        },
    }

    def getOwner(self, request):
        """
            Overrides the getOwner method to set the
            current user object as owner instead of the creator
            Oneself will be always owner of oneself
        """
        if hasattr(self, 'username'):
            return self.username

        return self.data.get('username', request.creator)

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
            Subscribes the user to the context
        """
        subscription = context.prepareUserSubscription()
        self.add_to_list(context.user_subscription_storage, subscription, safe=False)
        context._after_subscription_add(self.username)

    def removeSubscription(self, context):
        """
            Unsubscribes the user from the context
        """
        self.delete_from_list(context.user_subscription_storage, {context.unique.lstrip('_'): context.getIdentifier()})
        context._after_subscription_remove(self.username)

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

    def updateConversationParticipants(self, force_update=False):
        """
            Updates participants list in user's subscriptions to conversations with updates in the original user
            Now only updates displayName
            Updates will only occur if the fields changed, to force the update, set force_update=True
        """
        updatable_fields = ['displayName']
        has_updatable_fields = set(updatable_fields).intersection(self.data.keys())

        if has_updatable_fields or force_update:
            if 'displayName' in self.schema.keys() and (self.field_changed('displayName') or force_update):
                self.mdb_collection.database.conversations.update({'participants.username': self.username}, {'$set': {'participants.$.displayName': self.displayName}}, multi=True)

    def grantPermission(self, subscription, permission, permanent=DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY):
        """
        Grant a permission on a context's user subscription.

        Grants will persist over context default permission changes based on permanent parameter.
        Non permament permission grant, will remove vetos!
        """
        criteria = {}

        # Add current permissions
        new_permissions = list(subscription['permissions'])

        # Add new permission if not present
        if permission not in new_permissions:
            new_permissions.append(permission)

        # Persist permissions across changes on context
        if permanent:
            # Add permission to grants if not present
            subscription.setdefault('_grants', [])
            if permission not in subscription['_grants']:
                subscription['_grants'].append(permission)

        # Remove permission from vetos if present, always
        subscription.setdefault('_vetos', [])
        subscription['_vetos'] = [vetted for vetted in subscription['_vetos'] if vetted != permission]

        # Get a dummy context from subscription to determine the fields to update
        ContextClass = getMaxModelByObjectType(subscription['objectType'])
        temp_context = ContextClass()
        context_unique_field = temp_context.unique.lstrip('_')
        temp_context.fromObject({
            context_unique_field: subscription[context_unique_field],
            'objectType': subscription['objectType']
        })

        context_storage_field = temp_context.user_subscription_storage
        subscription_unique_field = '{}.{}'.format(context_storage_field, context_unique_field)

        criteria.update({subscription_unique_field: subscription[context_unique_field]})   # update object that matches hash
        criteria.update({'_id': self._id})                 # of collection entry with _id

        # overwrite permissions
        what = {
            '$set': {
                '{}.$.permissions'.format(context_storage_field): new_permissions,
                '{}.$._grants'.format(context_storage_field): subscription.get('_grants', []),
                '{}.$._vetos'.format(context_storage_field): subscription.get('_vetos', [])
            }
        }

        self.mdb_collection.update(criteria, what)

        # update subscription permissions
        subscription['permissions'] = new_permissions
        fields_to_squash = ['published', 'owner', 'creator', 'tags', 'vetos', 'grants']
        subscription = flatten(subscription, squash=fields_to_squash)

        return subscription

    def revokePermission(self, subscription, permission, permanent=DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY):
        """
        Revoke a permission on a context's user subscription.

        Revokes will persist over context default permission changes based on permanent parameter.
        Non permanent permission revoke will remove grants!

        """
        criteria = {}
        new_permissions = []

        # Add current permissions except revoked one
        new_permissions = [p for p in subscription['permissions'] if permission != p]

        if permanent:
            # Add permission to vetos if not present
            subscription.setdefault('_vetos', [])
            if permission not in subscription['_vetos']:
                subscription['_vetos'].append(permission)

        # Remove permission from grants if present
        subscription.setdefault('_grants', [])
        subscription['_grants'] = [granted for granted in subscription['_grants'] if granted != permission]

        # Get a dummy context from subscription to determine the fields to update
        ContextClass = getMaxModelByObjectType(subscription['objectType'])
        temp_context = ContextClass()
        context_unique_field = temp_context.unique.lstrip('_')
        temp_context.fromObject({
            context_unique_field: subscription[context_unique_field],
            'objectType': subscription['objectType']
        })

        context_storage_field = temp_context.user_subscription_storage
        subscription_unique_field = '{}.{}'.format(context_storage_field, context_unique_field)

        criteria.update({subscription_unique_field: subscription[context_unique_field]})   # update object that matches hash
        criteria.update({'_id': self._id})                 # of collection entry with _id

        # overwrite permissions

        what = {
            '$set': {
                '{}.$.permissions'.format(context_storage_field): new_permissions,
                '{}.$._grants'.format(context_storage_field): subscription.get('_grants', []),
                '{}.$._vetos'.format(context_storage_field): subscription.get('_vetos', [])
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
            if subscription[temp_context.unique.lstrip('_')] == str(temp_context[temp_context.unique]):
                return subscription

    def addUserDevice(self, platform, token):
        self.add_to_list(platform + PLATFORM_FIELD_SUFFIX, token)

    def deleteUserDevice(self, platform, token):
        self.delete_from_list(platform + PLATFORM_FIELD_SUFFIX, token)

    def deleteUserDevices(self, platform):
        self[platform + PLATFORM_FIELD_SUFFIX] = []
        self.save()

    def isAllowedToSee(self, user):
        """
        NonVisible People can see Visible and NonVisible people
        Visible People only can see Visible People
        If the restricted mode is on, a shared context is neeed plus the latter affirmations
        """

        in_restricted_visibility_mode = asbool(self.request.registry.max_settings.get('max_restricted_user_visibility_mode', False))

        non_visible_user_list = self.request.registry.max_security.get('roles', {}).get('NonVisible', [])
        i_am_visible = self['username'] not in non_visible_user_list
        user_is_visible = user['username'] not in non_visible_user_list

        # I'm a visible person, so i should not see NonVisible persons,
        # regardless of the subscriptions we share
        if i_am_visible and not user_is_visible:
            return False

        my_subcriptions = set([subscription['hash'] for subscription in self.subscribedTo])
        user_subcriptions = set([subscription['hash'] for subscription in user['subscribedTo']])
        have_subscriptions_in_common = my_subcriptions.intersection(user_subcriptions)

        # If we reach here,  maybe:
        #  - I am NonVisible and user NonVisible too
        #  - I amb NonVisible and user is visible
        #  - I am visible and so is the user
        # In any of the cases,
        # if restricted visibility is ON users MUST share at
        # least one subscription to see each other otherwise
        # they can see everybody

        if have_subscriptions_in_common or not in_restricted_visibility_mode:
            return True

        # We are in restricted mode without shared contexts with the user
        return False

    def getInfo(self):
        actor = self.flatten()
        if self.check_field_permission('talkingIn', 'view'):
            actor.setdefault('talkingIn', [])
            conversations_collection = MADMaxCollection(self.db.conversations)
            conversations = conversations_collection.search({'_id': {'$in': [ObjectId(conv['id']) for conv in actor['talkingIn']]}})
            conversations_by_id = {str(conv['_id']): conv for conv in conversations}
            for conversation in actor['talkingIn']:
                conversation_object = conversations_by_id[conversation['id']]
                conversation_object.fromObject(conversation)
                conversation['displayName'] = conversation_object.realDisplayName(self.username)
                conversation['lastMessage'] = conversation_object.lastMessage()

                conversation['participants'] = conversation_object.participants
                conversation['tags'] = conversation_object.tags

                conversation['messages'] = 0

            actor['talkingIn'] = sorted(actor['talkingIn'], reverse=True, key=lambda conv: conv['lastMessage']['published'])

        return actor

    def _on_insert_object(self, oid, notifications=True):
        """
            Create user exchanges just after user creation on the database
        """
        if notifications:
            notifier = RabbitNotifications(self.request)
            notifier.add_user(self.username)

    def _after_delete(self):
        """
            Deletes user exchanges just after user is deleted.
        """
        notifier = RabbitNotifications(self.request)
        notifier.delete_user(self.username)
