# -*- coding: utf-8 -*-
from max import DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY
from max.MADMax import MADMaxCollection
from max.MADObjects import MADBase
from max.rabbitmq import RabbitNotifications
from max.security import Manager
from max.security import Owner
from max.security import is_self_operation
from max.security.permissions import add_activity
from max.security.permissions import change_ownership
from max.security.permissions import delete_token
from max.security.permissions import list_activities
from max.security.permissions import list_activities_unsubscribed
from max.security.permissions import list_comments
from max.security.permissions import list_tokens
from max.security.permissions import modify_avatar
from max.security.permissions import modify_immutable_fields
from max.security.permissions import modify_user
from max.security.permissions import view_private_fields
from max.security.permissions import view_subscriptions
from max.security.permissions import view_user_profile
from max.security.permissions import view_timeline
from max.utils import getMaxModelByObjectType
from max.utils.dicts import flatten

from pyramid.decorator import reify
from pyramid.security import Allow
from pyramid.security import Authenticated
from pyramid.settings import asbool

from bson import ObjectId

import datetime


class User(MADBase):
    """
        An activitystrea.ms User object representation
    """
    default_field_view_permission = view_user_profile
    default_field_edit_permission = modify_user
    collection = 'users'
    unique = 'username'
    schema = {
        '_id': {
            'edit': modify_immutable_fields,
            'view': view_private_fields
        },
        '_creator': {
            'edit': modify_immutable_fields,
            'view': view_private_fields
        },
        '_owner': {
            'edit': change_ownership,
            'view': view_private_fields
        },
        'objectType': {
            'edit': modify_immutable_fields,
            'default': 'person'
        },
        'username': {
            'required': 1,
        },
        'displayName': {
        },
        'last_login': {
            'view': view_private_fields,
            'edit': modify_immutable_fields,
        },
        'following': {
            'view': view_subscriptions,
            'edit': modify_immutable_fields,
            'default': []
        },
        'subscribedTo': {
            'view': view_subscriptions,
            'edit': modify_immutable_fields,
            'default': []
        },
        'talkingIn': {
            'view': view_subscriptions,
            'edit': modify_immutable_fields,
            'default': []
        },
        'published': {
            'edit': modify_immutable_fields
        },
        'twitterUsername': {
            'formatters': ['stripTwitterUsername'],
            'validators': ['isValidTwitterUsername']
        },
    }

    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, list_activities),
            (Allow, Manager, list_activities_unsubscribed),
            (Allow, Manager, view_timeline),
            (Allow, Manager, add_activity),
            (Allow, Manager, view_subscriptions),
            (Allow, Manager, list_comments),
            (Allow, Manager, view_private_fields),
            (Allow, Manager, modify_avatar),
            (Allow, Manager, delete_token),
            (Allow, Manager, list_tokens),

            (Allow, Owner, modify_user),
            (Allow, Owner, view_timeline),
            (Allow, Owner, list_activities),
            (Allow, Owner, add_activity),
            (Allow, Owner, view_subscriptions),
            (Allow, Owner, list_comments),
            (Allow, Owner, view_private_fields),
            (Allow, Owner, modify_avatar),
            (Allow, Owner, delete_token),

            (Allow, Authenticated, view_user_profile),
            (Allow, Authenticated, list_activities),
        ]

        if is_self_operation(self.request):
            acl.append((Allow, self.request.authenticated_userid, list_tokens)),
            acl.append((Allow, self.request.authenticated_userid, view_subscriptions))

        return acl

    def format_unique(self, key):
        return key

    def getOwner(self, request):
        """
            Overrides the getOwner method to set the
            current user object as owner instead of the creator
            Oneself will be always owner of oneself. If not found,
            look for data being processed and finally default to creator.
        """
        return self.get('username', self.data.get('username', request.authenticated_userid))

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
        context._after_subscription_add(self['username'])

    def removeSubscription(self, context):
        """
            Unsubscribes the user from the context
        """
        self.delete_from_list(context.user_subscription_storage, {context.unique.lstrip('_'): context.getIdentifier()})
        context._after_subscription_remove(self['username'])

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
        criteria.update({'_id': self['_id']})                 # of collection entry with _id

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
                self.mdb_collection.database.conversations.update({'participants.username': self['username']}, {'$set': {'participants.$.displayName': self['displayName']}}, multi=True)

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
        context_unique_field = ContextClass.unique.lstrip('_')
        temp_context = ContextClass.from_object(
            self.request,
            {
                context_unique_field: subscription[context_unique_field],
                'objectType': subscription['objectType']
            }
        )

        context_storage_field = temp_context.user_subscription_storage
        subscription_unique_field = '{}.{}'.format(context_storage_field, context_unique_field)

        criteria.update({subscription_unique_field: subscription[context_unique_field]})   # update object that matches hash
        criteria.update({'_id': self['_id']})                 # of collection entry with _id

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
        context_unique_field = ContextClass.unique.lstrip('_')
        temp_context = ContextClass.from_object(
            self.request,
            {
                context_unique_field: subscription[context_unique_field],
                'objectType': subscription['objectType']
            }
        )

        context_storage_field = temp_context.user_subscription_storage
        subscription_unique_field = '{}.{}'.format(context_storage_field, context_unique_field)

        criteria.update({subscription_unique_field: subscription[context_unique_field]})   # update object that matches hash
        criteria.update({'_id': self['_id']})                 # of collection entry with _id

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
        subscription_object_type = context.get('objectType', None)
        if subscription_object_type is None:
            return None

        ContextClass = getMaxModelByObjectType(subscription_object_type)
        temp_context = ContextClass.from_object(self.request, context)

        for subscription in self.get(temp_context.user_subscription_storage, []):
            if subscription.get(temp_context.unique.lstrip('_')) == str(temp_context[temp_context.unique]):
                return subscription

    def get_tokens(self, platform=None):
        """
            Returns all the tokens from a user, filtered by platform if any
        """

        tokens = MADMaxCollection(self.request, 'tokens')
        query = {
            '_owner': self['_owner'],
        }

        if platform is not None:
            query['platform'] = platform

        user_tokens = tokens.search(query)

        result = []
        for token in user_tokens:
            result.append(dict(token=token['token'], platform=token['platform'], username=token['_owner']))

        return result

    def delete_tokens(self, platform=None):
        """
            Deletes tokens from a user, filtered by platform if any
        """
        tokens = MADMaxCollection(self.request, 'tokens')
        query = {
            '_owner': self['_owner'],
        }

        if platform is not None:
            query['platform'] = platform

        tokens.remove(query)

    def is_allowed_to_see(self, user):
        """
        NonVisible People can see Visible and NonVisible people
        Visible People only can see Visible People
        If the restricted mode is on, a shared context is neeed plus the latter affirmations
        """

        in_restricted_visibility_mode = asbool(self.request.registry.max_settings.get('max_restricted_user_visibility_mode', False))

        non_visible_user_list = self.request.registry.max_security.get_role_users('NonVisible')
        i_am_visible = self['username'] not in non_visible_user_list
        user_is_visible = user['username'] not in non_visible_user_list

        # I'm a visible person, so i should not see NonVisible persons,
        # regardless of the subscriptions we share
        if i_am_visible and not user_is_visible:
            return False

        my_subcriptions = set([subscription['hash'] for subscription in self['subscribedTo']])
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
        if self.has_field_permission('talkingIn', 'view'):
            actor.setdefault('talkingIn', [])

            if actor['talkingIn']:
                conversation_objectids = [ObjectId(conv['id']) for conv in actor['talkingIn']]
                conversations_collection = MADMaxCollection(self.request, 'conversations')
                conversations = conversations_collection.search({'_id': {'$in': conversation_objectids}})
                conversations_by_id = {str(conv['_id']): conv for conv in conversations}

                messages_collection = MADMaxCollection(self.request, 'messages').collection

                pipeline = [
                    {"$match": {"contexts.id": {"$in": conversations_by_id.keys()}}},
                    {"$sort": {"_id": 1}},
                    {"$group": {
                        "_id": "$contexts.id",
                        "object": {"$last": "$object"},
                        "published": {"$last": "$published"}
                    }}
                ]
                messages = messages_collection.aggregate(pipeline)['result']

                def format_message(db_message):
                    message_object = db_message.get('object', {})
                    message = dict(
                        objectType=message_object.get('objectType', 'note'),
                        content=message_object.get('content', ''),
                        published=db_message.get('published', '')
                    )

                    if isinstance(message['published'], datetime.datetime):
                        try:
                            message['published'] = message['published'].isoformat()
                        except:
                            message['published'] = message['published']

                    # Set object urls for media types
                    if message['objectType'] in ['file', 'image']:
                        message['fullURL'] = message_object.get('fullURL', '')
                        if message['objectType'] == 'image':
                            message['thumbURL'] = message_object.get('thumbURL', '')

                    return message
                messages_by_conversation = {message['_id'][0]: format_message(message) for message in messages}
                for subscription in actor['talkingIn']:
                    conversation_object = conversations_by_id[subscription['id']]
                    subscription['displayName'] = conversation_object.realDisplayName(self['username'])
                    subscription['lastMessage'] = messages_by_conversation[subscription['id']]
                    subscription['participants'] = conversation_object['participants']
                    subscription['tags'] = conversation_object['tags']
                    subscription['messages'] = 0

                actor['talkingIn'] = sorted(actor['talkingIn'], reverse=True, key=lambda conv: conv['lastMessage']['published'])

        return actor

    def getConversations(self):
        """
            Get user conversations
        """
        # List subscribed conversations, and use it to make the query
        # This way we can filter 2-people conversations that have been archived
        subscribed_conversations = [ObjectId(subscription.get('id')) for subscription in self.request.actor.get('talkingIn', [])]

        query = {'participants.username': self['username'],
                 'objectType': 'conversation',
                 '_id': {'$in': subscribed_conversations}
                 }

        conversations_search = self.request.db.conversations.search(query, sort_by_field="published")

        return conversations_search

    def _after_insert_object(self, oid, notifications=True):
        """
            Create user exchanges just after user creation on the database
        """
        query = {
            'objectType': 'conversation',
            'participants.username': self['username']
        }

        conversations_search = self.request.db.conversations.search(query)
        for conversation in conversations_search:
            if len(conversation['participants']) == 2:
                if 'group' not in conversation['tags']:
                    if 'archive' in conversation['tags']:
                        conversation['tags'].remove('archive')
                        conversation['tags'].append('single')
                        conversation.save()

        if notifications:
            notifier = RabbitNotifications(self.request)
            notifier.add_user(self['username'])

    def _before_delete(self):
        """
            Executed before an object removal
            Override to provide custom behaviour on delete
        """
        query = {
            'objectType': 'conversation',
            'participants.username': self['username']
        }

        conversations_search = self.request.db.conversations.search(query)
        for conversation in conversations_search:
            self.removeSubscription(conversation)
            if 'single' in conversation['tags']:
                conversation['tags'].remove('single')
                conversation['tags'].append('archive')
                conversation.save()

    def _after_delete(self):
        """
            Deletes user exchanges just after user is deleted.
        """
        notifier = RabbitNotifications(self.request)
        notifier.delete_user(self['username'])
