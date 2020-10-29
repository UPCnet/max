# -*- coding: utf-8 -*-
from max import DEFAULT_CONTEXT_PERMISSIONS
from max.MADMax import MADMaxCollection
from max.MADObjects import MADBase
from max.models.user import User
from max.rabbitmq import RabbitNotifications
from max.security import Manager
from max.security import Owner
from max.security import is_self_operation
from max.security import permissions
from max.utils.twitter import get_twitter_api
from max.utils.twitter import get_userid_from_twitter

from pyramid.decorator import reify
from pyramid.security import Allow
from pyramid.security import Authenticated

from hashlib import sha1


class BaseContext(MADBase):
    """
        A max Context object representation
    """
    default_field_view_permission = permissions.view_context
    default_field_edit_permission = permissions.modify_context
    updatable_fields = ['permissions', 'displayName']
    unique = '_id'
    uniqueMethod = None
    schema = {
        '_id': {},
        '_creator': {},
        '_owner': {},
        'objectType': {
            'default': 'context'
        },
        'displayName': {
        },
        'published': {},
        'permissions': {
            'default': {
                'read': DEFAULT_CONTEXT_PERMISSIONS['read'],
                'write': DEFAULT_CONTEXT_PERMISSIONS['write'],
                'subscribe': DEFAULT_CONTEXT_PERMISSIONS['subscribe'],
                'invite': DEFAULT_CONTEXT_PERMISSIONS['invite']
            },
        }
    }

    def getOwner(self, request):
        """
            Overrides the getOwner method to set the
            owner as the current _owner as the owner.
            If not found,look for data being processed wiht param "owner"
            and finally default to creator.
        """
        return self.get('_owner', self.data.get('owner', request.authenticated_userid))

    def getIdentifier(self):
        return str(self[self.unique])

    def buildObject(self):
        """
            Updates the dict content with the context structure,
            with data from the request
        """

        # Update properties from request data if defined in schema
        # Also create properties with a default value defined
        ob = {}
        properties = {}
        for key, value in self.schema.items():
            default = value.get('default', None)
            if key in self.data:
                properties[key] = self.data[key]
            elif 'default' in value.keys():
                properties[key] = default
        ob.update(properties)

        self.update(ob)

    def modifyContext(self, properties):
        """Update the user object with the given properties"""
        self.updateFields(properties)
        self.save()

    def subscribedUsers(self):
        """
        """
        criteria = {'{}.{}'.format(self.user_subscription_storage, self.unique.lstrip('_')): self.getIdentifier()}
        subscribed_users = self.mdb_collection.database.users.find(criteria)
        return [user for user in subscribed_users]

    def unSubscribedPushUsers(self):
        """
        """
        criteria = {'{}.{}'.format(self.user_unsubscription_storage_push, self.unique.lstrip('_')): self.getIdentifier()}
        subscribed_users = self.mdb_collection.database.users.find(criteria)
        return [user for user in subscribed_users]

    def prepareUserSubscription(self):
        """
        """
        fields_to_squash = ['published', 'owner', 'creator', 'uploadURL']
        if '_id' != self.unique:
            fields_to_squash.append('_id')
        subscription = self.flatten(squash=fields_to_squash)

        # Add subscription permissions based on defaults and context values
        user_permissions = self.subscription_permissions(base=[])

        # Assign permissions to the subscription object before adding it
        subscription['permissions'] = user_permissions
        return subscription

    def get_permission_policy(self, permission, default):
        """
            Returns the effective policy that will be used to grant the permisison

            The unsubscribe policy has a special treatment:
            - If the permission is explicitly specified, the context policy will be used
            - If no unsubscribe policy is found, but the subscribe one is, subscribe policy will be used
            - If neither unsubscribe or subscribe policy found, default unsubscribe policy will be used.
        """
        if permission == 'unsubscribe':
            policy = self['permissions'].get(permission, None)
            if policy is None:
                policy = self.get_permission_policy('subscribe', default)
        else:
            policy = self['permissions'].get(permission, default)

        return policy

    def subscription_permissions(self, base=[]):
        """
            Return a list of granted permissions on this context.

            To construct the list, three (maximum) possible sources will be looked up
            in the following order. For each of max contexts existing permissions. Once
            a value is found, the rest won't be looked up, and so not overriden.

            1. Provided base permissions
            2. Context permission policy for that permission, will grant it not restricted to.
            2. Default policy for that permission, will grant it not restricted to.
        """
        user_permissions = list(base)

        for permission, default in DEFAULT_CONTEXT_PERMISSIONS.items():
            if permission not in user_permissions:
                context_grants_permission = self.get_permission_policy(permission, default) != 'restricted'
                if context_grants_permission:
                    user_permissions.append(permission)

        return user_permissions

    def updateContextActivities(self, force_update=False):
        """
            Updates context's activities with changes of the original context
            Now only updates displayName and permissions
            Updates will only occur if the fields changed, to force the update, set force_update=True
        """
        updatable_fields = ['displayName', 'tags', 'url']
        has_updatable_fields = set(updatable_fields).intersection(self.data.keys())

        if has_updatable_fields or force_update:
            criteria = {'contexts.{}'.format(self.unique.lstrip('_')): self.getIdentifier()}
            updates = {}

            if 'displayName' in self.schema.keys() and (self.field_changed('displayName') or force_update):
                updates.update({'contexts.$.displayName': self['displayName']})

            if 'tags' in self.schema.keys() and (self.field_changed('tags') or force_update):
                updates.update({'contexts.$.tags': self.get('tags')})

            if 'participants' in self.schema.keys() and (self.field_changed('participants') or force_update):
                updates.update({'contexts.$.participants': self['participants']})

            if 'url' in self.schema.keys() and (self.field_changed('url') or force_update):
                updates.update({'contexts.$.url': self['url']})
                updates.update({'contexts.$.hash': self['hash']})

            combined_updates = {'$set': updates}

            self.mdb_collection.database[self.activity_storage].update(criteria, combined_updates, multi=True)

    def updateUsersSubscriptions(self, force_update=False):
        """
            Updates users subscriptions with changes of the original context.
            Now only updates displayName and permissions and tags
            Updates will only occur if the fields changed, to force the update, set force_update=True
        """
        if force_update:
            must_update_fields = self.updatable_fields
        else:
            fields_with_update_request = set(self.updatable_fields).intersection(self.data.keys())
            must_update_fields = [field for field in fields_with_update_request if self.field_changed(field)]

        # Construct a list of all updatable fields that has changes. On force_update=True, all
        # fields with requested update will pass trough

        if must_update_fields:
            for user in self.subscribedUsers():
                user_object = User.from_object(self.request, user)
                criteria = {'_id': user['_id'], '{}.{}'.format(self.user_subscription_storage, self.unique.lstrip('_')): self.getIdentifier()}
                updates = {}

                if 'url' in must_update_fields:
                    updates.update({'{}.$.url'.format(self.user_subscription_storage): self['url']})
                    updates.update({'{}.$.hash'.format(self.user_subscription_storage): self['hash']})

                if 'displayName' in must_update_fields:
                    updates.update({'{}.$.displayName'.format(self.user_subscription_storage): self['displayName']})

                if 'tags' in must_update_fields:
                    updates.update({'{}.$.tags'.format(self.user_subscription_storage): self.get('tags', [])})

                if 'notifications' in must_update_fields:
                    updates.update({'{}.$.notifications'.format(self.user_subscription_storage): self.get('notifications', False)})

                if 'participants' in must_update_fields:
                    updates.update({'{}.$.participants'.format(self.user_subscription_storage): self['participants']})

                if 'permissions' in must_update_fields:
                    subscription = user_object.getSubscription(self)
                    _vetos = subscription.get('_vetos', [])
                    _grants = subscription.get('_grants', [])

                    # The default permissions from the new configured context
                    new_permissions = self.subscription_permissions()

                    # First add the persistent granted permissions
                    for granted_permission in _grants:
                        if granted_permission not in new_permissions:
                            new_permissions.append(granted_permission)

                    # Then rebuild list excluding the vetted permissions
                    # except if the permission is also granted
                    # This way, the vetted permissions will disappear, and the plain ones
                    # will remain untouched
                    new_permissions = [permission for permission in new_permissions if (permission not in _vetos or permission in _grants)]

                    updates.update({'{}.$.permissions'.format(self.user_subscription_storage): new_permissions})

                if updates:
                    combined_updates = {'$set': updates}
                    self.mdb_collection.database.users.update(criteria, combined_updates, multi=True)

                # update original subscriptions related to this user when changing url
                if self.field_changed('url'):
                    self.field_changed('url')
                    self.mdb_collection.database.activity.update(
                        {'actor.username': user['username'], 'object.url': self.old['url']},
                        {'$set': {
                            'object.url': self['url'],
                            'object.hash': self['hash'],
                        }},
                        multi=True
                    )

                self.save()

    def removeUserSubscriptions(self, users_to_delete=[]):
        """
            Removes all users subscribed to the context, or only specifiyed
            user if userd_to_delete is provided
        """
        usersdb = MADMaxCollection(self.request, 'users')
        criteria = {'{}.{}'.format(self.user_subscription_storage, self.unique.lstrip('_')): self.getIdentifier()}
        users = usersdb.search(criteria)

        for user in users:
            if users_to_delete == [] or user['username'] in users_to_delete:
                user.removeSubscription(self)

    def removeUnsubscriptionPush(self, users_to_delete=[]):
        """
            Removes all users subscribed to the context, or only specifiyed
            user if userd_to_delete is provided
        """
        usersdb = MADMaxCollection(self.request, 'users')
        criteria = {'{}.{}'.format(self.user_unsubscription_storage_push, self.unique.lstrip('_')): self.getIdentifier()}
        users = usersdb.search(criteria)

        for user in users:
            if users_to_delete == [] or user['username'] in users_to_delete:
                user.removeUnsubscriptionPush(self)

    def removeActivities(self, logical=False):
        """
            Removes all activity posted to a context. If logical is set to True
            Activities are not actually deleted, only marked as not visible
        """
        activitydb = MADMaxCollection(self.request, self.activity_storage)
        which_to_delete = {
            'contexts.{}'.format(self.unique.lstrip('_')): self.getIdentifier()
        }
        activitydb.remove(which_to_delete, logical=logical)

    @property
    def subscription(self):
        """
            Retrieves the current actor susbcription to this context.

            If the actor is a context, don't return any subscription
        """
        if hasattr(self.request.actor, 'getSubscription'):
            return self.request.actor.getSubscription(self)

    def getInfo(self):
        context = self.flatten()
        context.setdefault('permissions', {})
        for permission, value in DEFAULT_CONTEXT_PERMISSIONS.items():
            context['permissions'][permission] = context['permissions'].get(permission, value)

        return context

    def _after_subscription_add(self, username):
        """
            Executed after a user has been subscribed to this context
            Override to add custom behaviour for each context type
        """
        pass  # pragma: no cover

    def _after_subscription_remove(self, username):
        """
            Executed after a user has been unsubscribed to this context
            Override to add custom behaviour for each context type
        """
        pass  # pragma: no cover


class Context(BaseContext):
    """
        A context containing a Uri
    """
    default_field_view_permission = permissions.view_context
    default_field_edit_permission = permissions.modify_context

    updatable_fields = ['notifications', 'permissions', 'displayName', 'tags', 'url']
    collection = 'contexts'
    unique = 'hash'
    user_subscription_storage = 'subscribedTo'
    user_unsubscription_storage_push = 'unsubscribedToPush'
    activity_storage = 'activity'
    schema = dict(BaseContext.schema)
    schema['hash'] = {}
    schema['url'] = {'required': 1}
    schema['tags'] = {'default': []}
    schema['twitterHashtag'] = {
        'formatters': ['stripHash'],
        'validators': ['isValidHashtag'],
    }
    schema['twitterUsername'] = {
        'formatters': ['stripTwitterUsername'],
        'validators': ['isValidTwitterUsername'],
    }
    schema['twitterUsernameId'] = {
    }
    schema['notifications'] = {
        'default': False
    }

    schema['uploadURL'] = {}

    @reify
    def __acl__(self):
        acl = [
            (Allow, Authenticated, permissions.view_context),
            (Allow, Owner, permissions. modify_context),
            (Allow, Owner, permissions.delete_context),
            (Allow, Manager, permissions.add_subscription),
            (Allow, Owner, permissions.add_subscription),
            (Allow, Manager, permissions.list_activities),
            (Allow, Manager, permissions.list_activities_unsubscribed),
            (Allow, Owner, permissions.list_activities),
            (Allow, Manager, permissions.add_activity),
            (Allow, Manager, permissions.list_comments),

            (Allow, Manager, permissions.manage_subcription_permissions),
            (Allow, Owner, permissions.manage_subcription_permissions),
            (Allow, Manager, permissions.remove_subscription),
            (Allow, Owner, permissions.remove_subscription),
        ]
        # Grant subscribe permission to the user to subscribe itself if the context policy allows it
        if self['permissions'].get('subscribe', DEFAULT_CONTEXT_PERMISSIONS['subscribe']) == 'public' and is_self_operation(self.request):
            acl.append((Allow, self.request.authenticated_userid, permissions.add_subscription))

        # Grant view activities
        if self['permissions'].get('read', DEFAULT_CONTEXT_PERMISSIONS['read']) == 'public':
            acl.append((Allow, self.request.authenticated_userid, permissions.list_activities))

        # Granted permissions only if a subscription for the current actor exists
        if self.subscription:

            # Grant permisions only available if subscription exists. Setting this permissions
            # conditionally here, causes a Forbidden to be raised when trying to modify or delete
            # an inexistent subscription, event if you're a Owner or Manager.
            # acl.extend([
            #     (Allow, Manager, permissions.manage_subcription_permissions),
            #     (Allow, Owner, permissions.manage_subcription_permissions),
            #     (Allow, Manager, permissions.remove_subscription),
            #     (Allow, Owner, permissions.remove_subscription),
            # ])

            # Grant ubsubscribe permission if the user subscription allows it
            # but only if is trying to unsubscribe itself.
            if 'unsubscribe' in self.subscription.get('permissions', []) and is_self_operation(self.request):
                acl.append((Allow, self.request.authenticated_userid, permissions.remove_subscription))

            # Grant add_activity permission if the user subscription allows it
            # but only if is trying to post as himself. This avoids Context owners to create
            # activity impersonating othe users
            if 'write' in self.subscription.get('permissions', []) and is_self_operation(self.request):
                acl.append((Allow, self.request.authenticated_userid, permissions.add_activity))

            # Grant list_activities permission if the user subscription allows it
            if 'read' in self.subscription.get('permissions', []):
                acl.append((Allow, self.request.authenticated_userid, permissions.list_activities))
                acl.append((Allow, self.request.authenticated_userid, permissions.list_comments))
            return acl

        return acl

    def alreadyExists(self):
        """
            Checks if there's an object with the value specified in the unique field.
            If present, return the object, otherwise returns None
        """
        unique = self.unique
        if self.unique in self:
            value = self[self.unique]
        elif self.unique not in self.data.keys():
            value = self.data.get('url', '')
            value = sha1(value).hexdigest()
        else:
            value = self.data.get(unique)

        if value:
            query = {unique: value}
            return self.mdb_collection.find_one(query)
        else:
            # in the case that we don't have the unique value in the request data
            # Assume that the object doesn't exist
            # XXX TODO - Test it!!
            return None

    def _post_init_from_object(self, source):
        if self.get(self.unique, None) is None:
            self[self.unique] = self.getIdentifier()

    def format_unique(self, key):
        return key

    def getIdentifier(self):
        """
            Resolves a valid identifier from this context. Different attemps will be
            made, based on different possible status of the context

            1. Try to get the hash from the object
            2. If the context has url field and it's set, calculate the hash

        """
        chash = self.get('hash', None)

        url = self.get('url', None)
        if 'url' in self.schema.keys() and url:
            if self.field_changed('url'):
                return self.old.get('hash', sha1(self['url']).hexdigest())
            else:
                return sha1(self['url']).hexdigest()

        return chash

    def buildObject(self):
        super(Context, self).buildObject()

        # If creating with the twitterUsername, get its Twitter ID
        if self.data.get('twitterUsername', None):
            api = get_twitter_api(self.request.registry)
            self['twitterUsernameId'] = get_userid_from_twitter(api, self.data['twitterUsername'])

        self['hash'] = self.getIdentifier()

        # Set displayName only if it's not specified
        self['displayName'] = self.get('displayName', self['url'])

    def modifyContext(self, properties):
        """Update the user object with the given properties"""
        # If updating the twitterUsername, get its Twitter ID
        if properties.get('twitterUsername', None):
            api = get_twitter_api(self.request.registry)
            properties['twitterUsernameId'] = get_userid_from_twitter(api, properties['twitterUsername'])

        self.updateFields(properties)

        if self.get('twitterUsername', None) is None and self.get('twitterUsernameId', None) is not None:
            del self['twitterUsernameId']

        # someone changed notifications settings for this context
        if 'notifications' in properties:
            notifier = RabbitNotifications(self.request)
            if self.get('notifications', False):
                for user in self.subscribedUsers():
                    notifier.bind_user_to_context(self, user['username'])
            else:
                for user in self.subscribedUsers():
                    notifier.unbind_user_from_context(self, user['username'])

        if 'url' in properties:
            self['hash'] = sha1(self['url']).hexdigest()

        self.save()

    def _after_insert_object(self, oid):
        if self.field_changed('twitterUsername'):
            notifier = RabbitNotifications(self.request)
            notifier.restart_tweety()

    def _after_saving_object(self, oid):
        if self.field_changed('twitterUsername'):
            notifier = RabbitNotifications(self.request)
            notifier.restart_tweety()

    def _after_subscription_add(self, username):
        """
            Creates rabbitmq bindings after new subscription
        """
        if self.get('notifications', False):
            notifier = RabbitNotifications(self.request)
            notifier.bind_user_to_context(self, username)

    def _after_subscription_remove(self, username):
        """
            Removes rabbitmq bindings after new subscription
        """
        notifier = RabbitNotifications(self.request)
        notifier.unbind_user_from_context(self, username)
