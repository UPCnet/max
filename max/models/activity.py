# -*- coding: utf-8 -*-
import datetime
from hashlib import sha1

from max.MADObjects import MADBase
from max.MADMax import MADMaxCollection
from max.models.user import User
from max.models.context import Context
from max.rest.utils import canWriteInContexts, hasPermission


class BaseActivity(MADBase):
    """
        An activitystrea.ms Activity object representation
    """
    unique = '_id'
    schema = {'_id':         dict(required=0),
              '_creator':    dict(required=0),
              '_owner':      dict(required=0),
              'objectType':  dict(required=0, default='activity'),
              'actor':       dict(required=1),
              'verb':        dict(required=1),
              'object':      dict(required=1),
              'published':   dict(required=0),
              'commented':   dict(required=0),
              'contexts':    dict(required=0),
              'replies':     dict(required=0, default=[]),
              'generator':   dict(required=0, default=None),
              }

    def setDates(self):
        super(BaseActivity, self).setDates()
        self['commented'] = datetime.datetime.utcnow()

    def getOwner(self, request):
        """
            Overrides the getOwner method to set the
            actor as owner instead of the creator whenever
            the actor is a person
        """
        isPerson = isinstance(self.data['actor'], User)
        isContext = isinstance(self.data['actor'], Context)

        if isPerson:
            return request.actor['username']
        elif isContext:
            return request.creator

    def buildObject(self):
        """
            Updates the dict content with the activity structure,
            with data parsed from the request
        """

        isPerson = isinstance(self.data['actor'], User)
        isContext = isinstance(self.data['actor'], Context)

        # XXX Assuming here we only support Person as user
        # XXX Assuming here we only support Uri as context
        actorType = isPerson and 'person' or 'uri'
        ob = {'actor': {'objectType': actorType,
                        'displayName': self.data['actor']['displayName'],
                        },
              'verb': self.data['verb'],
              'object': None,
              }
        if isPerson:
            ob['actor']['username'] = self.data['actor']['username']
        elif isContext:
            ob['actor']['hash'] = self.data['actor']['hash']
            ob['actor']['url'] = self.data['actor']['url']

        wrapper = self.getObjectWrapper(self.data['object']['objectType'])
        subobject = wrapper(self.data['object'])
        ob['object'] = subobject

        #Append actor as username if object has keywords and actor is a Person
        if ob['object'].get('_keywords', None):
            if isPerson:
                ob['object']['_keywords'].append(self.data['actor']['username'])

        if isPerson and 'contexts' in self.data:
            # When a person posts an activity it can be targeted
            # to multiple contexts. here we construct the basic info
            # of each context and store them in contexts key
            ob['contexts'] = []
            for cobject in self.data['contexts']:
                subscription = dict(self.data['actor'].getSubscription(cobject))

                #Clean innecessary fields
                non_needed_subscription_fields = ['tags', 'published', 'permissions', 'id', '_vetos', '_grants']
                for fieldname in non_needed_subscription_fields:
                    if fieldname in subscription:
                        del subscription[fieldname]
                ob['contexts'].append(subscription)
        if isContext:
            # When a context posts an activity it can be posted only
            # to itself, so add it directly
                ob['contexts'] = [self.data['actor'], ]
        self.update(ob)

        # Set defaults
        properties = {}
        for key, value in self.schema.items():
            default = value.get('default', None)
            # Value is in the request but not set yet, set it please.
            if key in self.data and key not in self:
                properties[key] = self.data[key]
            # Value is not in the request and we have a default, set it please
            elif 'default' in value.keys():
                properties[key] = default
        self.update(properties)

    def modifyActivity(self, properties):
        """Update the Activity object with the given properties"""

        self.updateFields(properties)
        self.save()

    def get_comment(self, commentid):
        comments = [comment for comment in self.replies if comment['id'] == commentid]
        return comments[0] if comments is not [] else False

    def addComment(self, comment):
        """
            Adds a comment to an existing activity and updates refering activity keywords and hashtags
        """

        #Clean innecessary fields
        non_needed_actor_fields = ['talkingIn', 'androidDevices', 'iosDevices', 'subscribedTo', 'following', 'last_login', '_id', 'published', 'twitterUsername']
        for fieldname in non_needed_actor_fields:
            if fieldname in comment['actor']:
                del comment['actor'][fieldname]

        self.add_to_list('replies', comment, allow_duplicates=True)

        activity_keywords = self.object.setdefault('_keywords', [])
        activity_keywords.extend(comment.get('_keywords', []))
        self.object['_keywords'] = list(set(activity_keywords))

        activity_hashtags = self.object.setdefault('_hashtags', [])
        activity_hashtags.extend(comment.get('_hashtags', []))
        self.object['_hashtags'] = list(set(activity_hashtags))
        self.commented = comment['published']

        self.save()

    def delete_comment(self, commentid):
        """
        """
        self.delete_from_list('replies', {'id': commentid})
        # XXX TODO Update activity hastags and keywords


class Activity(BaseActivity):
    """
        An activity
    """
    collection = 'activity'
    context_collection = 'contexts'
    unique = '_id'
    schema = dict(BaseActivity.schema)
    schema['deletable'] = dict(required=0)

    def _on_create_custom_validations(self):
        """
            Perform custom validations on the Activity Object

            * If the actor is a person, check wether can write in all contexts
            * If the actor is a context, check if the context is the same
        """
        collection = getattr(self.mdb_collection.database, self.context_collection)
        contextsdb = MADMaxCollection(collection, query_key='hash')

        # If we are updating, we already have all data on the object, so we read self directly
        result = True
        if isinstance(self.data['actor'], User):
            wrapped_contexts = []
            for context in self.data.get('contexts', []):
                # Get hash from context or calculate it from the url
                # XXX Too coupled ...
                chash = context.get('hash', None)
                if chash is None:
                    chash = sha1(context['url']).hexdigest()
                wrapped = contextsdb[chash]
                wrapped_contexts.append(wrapped)

            result = result and canWriteInContexts(self.data['actor'], wrapped_contexts)
        if self.data.get('contexts', None) and isinstance(self.data['actor'], Context):
            result = result and self.data['actor']['url'] == self.data.get('contexts')[0]
        return result

    def _post_init_from_object(self, source):
        """
            * Set the deletable flag on the object. If user is the owner don't check anything else,
            otherwhise, check if user has permissions to delete activities on that context
        """
        if self.request.actor is not None:
            # Execute only if we have a actor in the request. I we don't have a actor
            # probably (ehem) is a restricted function, and we don't need this flag.
            self['deletable'] = self.request.actor.username == self._owner
            if not self['deletable'] and self.get('contexts'):
                subscriptions_with_delete_permission = [subscription['hash'] for subscription in self.request.actor.subscribedTo if hasPermission(subscription,'delete')]
                for context in self.get('contexts'):
                    self['deletable'] = context['hash'] in subscriptions_with_delete_permission

            # Mark the comments with the deletable flag too
            for comment in self.replies:
                comment['deletable'] = self['deletable'] or self.request.actor.username == comment['actor']['username']
