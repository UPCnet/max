# -*- coding: utf-8 -*-
from max.MADObjects import MADBase
from max.MADMax import MADMaxCollection
from max.rest.utils import getUserIdFromTwitter
from max.models.user import User
from max import DEFAULT_CONTEXT_PERMISSIONS
from max.rabbitmq.notifications import restartTweety
from hashlib import sha1


class BaseContext(MADBase):
    """
        A max Context object representation
    """
    unique = '_id'
    uniqueMethod = None
    schema = {'_id':                dict(),
              '_creator':           dict(required=0),
              '_owner':             dict(required=0),
              'objectType':         dict(required=0, default='context'),
              'displayName':        dict(operations_mutable=1),
              'published':          dict(),
              'permissions':        dict(default={'read': DEFAULT_CONTEXT_PERMISSIONS['read'],
                                                  'write': DEFAULT_CONTEXT_PERMISSIONS['write'],
                                                  'subscribe': DEFAULT_CONTEXT_PERMISSIONS['subscribe'],
                                                  'invite': DEFAULT_CONTEXT_PERMISSIONS['invite']
                                                  },
                                         operations_mutable=1
                                         ),
              }

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

    def prepareUserSubscription(self):
        """
        """
        fields_to_squash = ['published', 'owner', 'creator']
        if '_id' != self.unique:
            fields_to_squash.append('_id')
        subscription = self.flatten(squash=fields_to_squash)

        #If we are subscribing the user, read permission is granted
        user_permissions = ['read']

        # Add subscription permissions based on defaults and context values
        user_permissions = self.subscription_permissions(base=user_permissions)

        #Assign permissions to the subscription object before adding it
        subscription['permissions'] = user_permissions
        return subscription

    def subscription_permissions(self, base=[]):
        user_permissions = list(base)
        if self.permissions.get('read', DEFAULT_CONTEXT_PERMISSIONS['read']) in ['subscribed', 'public']:
            user_permissions.append('read')
        if self.permissions.get('write', DEFAULT_CONTEXT_PERMISSIONS['write']) in ['subscribed', 'public']:
            user_permissions.append('write')
        if self.permissions.get('invite', DEFAULT_CONTEXT_PERMISSIONS['invite']) in ['subscribed']:
            user_permissions.append('invite')
        unsubscribe_permission = self.permissions.get('unsubscribe', self.permissions.get('subscribe', DEFAULT_CONTEXT_PERMISSIONS['subscribe']))
        if unsubscribe_permission in ['public']:
            user_permissions.append('unsubscribe')
        if self.permissions.get('delete', DEFAULT_CONTEXT_PERMISSIONS['delete'] in ['subscribed']):
            user_permissions.append('delete')

        return list(set(user_permissions))

    def updateContextActivities(self, force_update=False):
        """
            Updates context's activities with changes of the original context
            Now only updates displayName and permissions
            Updates will only occur if the fields changed, to force the update, set force_update=True
        """
        updatable_fields = ['displayName', 'tags']
        has_updatable_fields = set(updatable_fields).intersection(self.data.keys())

        if has_updatable_fields or force_update:
            criteria = {'contexts.{}'.format(self.unique.lstrip('_')): self.getIdentifier()}
            updates = {}

            if 'displayName' in self.schema.keys() and (self.field_changed('displayName') or force_update):
                updates.update({'contexts.$.displayName': self.displayName})

            if 'tags' in self.schema.keys() and (self.field_changed('tags') or force_update):
                updates.update({'contexts.$.tags': self.tags})

            if 'participants' in self.schema.keys() and (self.field_changed('participants') or force_update):
                updates.update({'contexts.$.participants': self.participants})

            combined_updates = {'$set': updates}

            self.mdb_collection.database[self.activity_storage].update(criteria, combined_updates, multi=True)

    def updateUsersSubscriptions(self, force_update=False):
        """
            Updates users subscriptions with changes of the original context.
            Now only updates displayName and permissions and tags
            Updates will only occur if the fields changed, to force the update, set force_update=True
        """
        updatable_fields = ['permissions', 'displayName', 'tags', 'participants']
        has_updatable_fields = set(updatable_fields).intersection(self.data.keys())

        if has_updatable_fields or force_update:
            for user in self.subscribedUsers():
                user_object = User()
                user_object.fromObject(user)
                criteria = {'_id': user['_id'], '{}.{}'.format(self.user_subscription_storage, self.unique.lstrip('_')): self.getIdentifier()}
                updates = {}

                if 'displayName' in self.schema.keys() and (self.field_changed('displayName') or force_update):
                    updates.update({'{}.$.displayName'.format(self.user_subscription_storage): self.displayName})

                if 'tags' in self.schema.keys() and (self.field_changed('tags') or force_update):
                    updates.update({'{}.$.tags'.format(self.user_subscription_storage): self.tags})

                if 'participants' in self.schema.keys() and (self.field_changed('participants') or force_update):
                    updates.update({'{}.$.participants'.format(self.user_subscription_storage): self.participants})

                if 'permissions' in self.schema.keys() and (self.field_changed('permissions') or force_update):
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

                combined_updates = {'$set': updates}
                self.mdb_collection.database.users.update(criteria, combined_updates, multi=True)

    def removeUserSubscriptions(self, users_to_delete=[]):
        """
            Removes all users subscribed to the context, or only specifiyed
            user if userd_to_delete is provided
        """
        usersdb = MADMaxCollection(self.mdb_collection.database.users)
        criteria = {'{}.{}'.format(self.user_subscription_storage, self.unique.lstrip('_')): self.getIdentifier()}
        users = usersdb.search(criteria)

        for user in users:
            if users_to_delete == [] or user.username in users_to_delete:
                user.removeSubscription(self)

    def removeActivities(self, logical=False):
        """
            Removes all activity posted to a context. If logical is set to True
            Activities are not actually deleted, only marked as not visible
        """
        activitydb = MADMaxCollection(getattr(self.mdb_collection.database, self.activity_storage))
        which_to_delete = {
            'contexts.{}'.format(self.unique.lstrip('_')): self.getIdentifier()
        }
        activitydb.remove(which_to_delete, logical=logical)


class Context(BaseContext):
    """
        A context containing a Uri
    """

    collection = 'contexts'
    unique = 'hash'
    user_subscription_storage = 'subscribedTo'
    activity_storage = 'activity'
    schema = dict(BaseContext.schema)
    schema['hash'] = dict()
    schema['url'] = dict(required=1)
    schema['tags'] = dict(default=[])
    schema['twitterHashtag'] = dict(operations_mutable=1,
                                    formatters=['stripHash'],
                                    validators=['isValidHashtag'],
                                    )
    schema['twitterUsername'] = dict(operations_mutable=1,
                                     formatters=['stripTwitterUsername'],
                                     validators=['isValidTwitterUsername'],
                                     )
    schema['twitterUsernameId'] = dict(operations_mutable=1)

    def alreadyExists(self):
        """
            Checks if there's an object with the value specified in the unique field.
            If present, return the object, otherwise returns None
        """
        unique = self.unique
        if self.unique not in self.data.keys():
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

    def getIdentifier(self):
        return sha1(self['url']).hexdigest()

    def buildObject(self):
        super(Context, self).buildObject()

        # If creating with the twitterUsername, get its Twitter ID
        if self.data.get('twitterUsername', None):
            self['twitterUsernameId'] = getUserIdFromTwitter(self.data['twitterUsername'])

        self['hash'] = self.getIdentifier()

        #Set displayName only if it's not specified
        self['displayName'] = self.get('displayName', self.url)

    def modifyContext(self, properties):
        """Update the user object with the given properties"""
        # If updating the twitterUsername, get its Twitter ID
        if properties.get('twitterUsername', None):
            properties['twitterUsernameId'] = getUserIdFromTwitter(properties['twitterUsername'])

        self.updateFields(properties)

        if self.get('twitterUsername', None) is None and self.get('twitterUsernameId', None) is not None:
            del self['twitterUsernameId']

        self.save()

    def _on_saving_object(self, oid):
        if self.field_changed('twitterUsername'):
            restartTweety()
