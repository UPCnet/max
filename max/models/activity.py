# -*- coding: utf-8 -*-
from bson import ObjectId
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
              '_keywords':   dict(required=0, default=[]),
              'objectType':  dict(required=0, default='activity'),
              'actor':       dict(required=1),
              'verb':        dict(required=1),
              'object':      dict(required=1),
              'published':   dict(required=0),
              'lastComment': dict(required=0),
              'contexts':    dict(required=0),
              'replies':     dict(required=0, default=[]),
              'generator':   dict(required=0, default=None),
              }

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
        # XXX Assuming here we only support Context as context
        actorType = isPerson and 'person' or 'context'
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

        if isPerson and 'contexts' in self.data:
            # When a person posts an activity it can be targeted
            # to multiple contexts. here we construct the basic info
            # of each context and store them in contexts key
            ob['contexts'] = []
            for cobject in self.data['contexts']:
                subscription = dict(self.data['actor'].getSubscription(cobject))

                #Clean innecessary fields
                non_needed_subscription_fields = ['published', 'permissions', 'id', '_vetos', '_grants']
                for fieldname in non_needed_subscription_fields:
                    if fieldname in subscription:
                        del subscription[fieldname]
                ob['contexts'].append(subscription)
        if isContext:
            # When a context posts an activity it can be posted only
            # to itself, so add it directly
            posted_context = dict(self.data['actor'])
            non_needed_context_fields = ['published', 'permissions', '_id', '_owner', '_creator', 'twitterHashtag']
            for fieldname in non_needed_context_fields:
                if fieldname in posted_context:
                    del posted_context[fieldname]

            ob['contexts'] = [posted_context, ]
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

        if self.verb in ['post']:
            self.setKeywords()

    def modifyActivity(self, properties):
        """Update the Activity object with the given properties"""

        self.updateFields(properties)
        self.save()

    def get_comment(self, commentid):
        comments = [comment for comment in self.replies if comment['id'] == commentid]
        return comments[0] if comments is not [] else False

    def setKeywords(self):
        #Append actor as username if object has keywords and actor is a Person
        self['_keywords'] = []
        self['_keywords'].extend(self.object.get('_keywords', []))
        if self.actor['objectType'] == 'person':
            self['_keywords'].append(self.actor['username'])
            self['_keywords'].extend(self.actor['username'].split('.'))
            self['_keywords'].extend(self.actor.get('displayName', '').lower().split())

        # Add keywords from comment objects
        replies = self.get('replies', [])
        for comment in replies:
            self['_keywords'].extend(comment.get('_keywords', []))
            self['_keywords'].append(comment['actor']['username'])
            self['_keywords'].extend(comment['actor']['username'].split('.'))
            self['_keywords'].extend(comment['actor'].get('displayName', '').lower().split())

        # delete duplicates
        self['_keywords'] = list(set(self['_keywords']))

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
        self.setKeywords()

        activity_hashtags = self.object.setdefault('_hashtags', [])
        activity_hashtags.extend(comment.get('_hashtags', []))
        self.object['_hashtags'] = list(set(activity_hashtags))
        self.lastComment = ObjectId(comment['id'])

        self.save()

    def delete_comment(self, commentid):
        """
        """
        self.delete_from_list('replies', {'id': commentid})
        self.replies = [comment for comment in self.replies if comment['id'] != commentid]
        self.setKeywords()
        self.save()
        # XXX TODO Update hastags


class Activity(BaseActivity):
    """
        An activity
    """
    collection = 'activity'
    context_collection = 'contexts'
    unique = '_id'
    schema = dict(BaseActivity.schema)
    schema['deletable'] = dict(required=0)
    schema['liked'] = dict(required=0)
    schema['favorited'] = dict(required=0)
    schema['likes'] = dict(required=0, default=[])
    schema['likesCount'] = dict(required=0, default=0)
    schema['favorites'] = dict(required=0, default=[])
    schema['favoritesCount'] = dict(required=0, default=0)

    def _on_saving_object(self, oid):
        if not hasattr(self, 'lastComment'):
            self.lastComment = oid
            self.save()

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

            * Set the liked and favorited flags on the object, with the number of each marks
        """
        if self.request.actor is not None:
            # Execute only if we have a actor in the request. I we don't have a actor
            # probably (ehem) is a restricted function, and we don't need this flag.

            if isinstance(self.request.actor, User):
                actor_id_field = 'username'
            else:
                actor_id_field = 'url'
            self['deletable'] = self.request.actor[actor_id_field] == self._owner
            if not self['deletable'] and self.get('contexts'):
                subscriptions_with_delete_permission = [subscription['hash'] for subscription in self.request.actor.get('subscribedTo', []) if hasPermission(subscription, 'delete')]
                for context in self.get('contexts'):
                    self['deletable'] = context['hash'] in subscriptions_with_delete_permission

            # Mark the comments with the deletable flag too
            for comment in self.get('replies', []):
                comment['deletable'] = self['deletable'] or self.request.actor[actor_id_field] == comment['actor']['username']

            self['favorited'] = self.has_favorite_from(self.request.actor)
            self['liked'] = self.has_like_from(self.request.actor)

    def add_favorite_from(self, actor):
        """
            Adds a favorite mark from somebody to an activity
        """
        prepared_actor = {
            actor.unique: actor.get(actor.unique),
            'objectType': actor.objectType
        }
        self.add_to_list('favorites', prepared_actor, allow_duplicates=False)
        self.favoritesCount = len(self.favorites)
        self.save()

    def add_like_from(self, actor):
        """
            Adds a like mark from somebody to an activity
        """
        prepared_actor = {
            actor.unique: actor.get(actor.unique),
            'objectType': actor.objectType
        }
        self.add_to_list('likes', prepared_actor, allow_duplicates=False)
        self.likesCount = len(self.likes)
        self.save()

    def delete_favorite_from(self, actor):
        """
            Deletes the favorite mark from somebody from an activity
        """
        self.delete_from_list('favorites', {actor.unique: actor.get(actor.unique)})
        self.favorites = [favorite for favorite in self.favorites if favorite[actor.unique] != actor[actor.unique]]
        self.favoritesCount = len(self.favorites)
        self.save()

    def delete_like_from(self, actor):
        """
            Deletes the like mark from somebody from an activity
        """
        self.delete_from_list('likes', {actor.unique: actor.get(actor.unique)})
        self.likes = [like for like in self.likes if like[actor.unique] != actor[actor.unique]]
        self.likesCount = len(self.likes)
        self.save()

    def has_like_from(self, actor):
        """
            Checks if the activity is already liked by this actor
        """
        actor_liked = [like_actor for like_actor in self.get('likes', []) if like_actor.get(actor.unique, None) == actor[actor.unique]]
        return True if actor_liked else False

    def has_favorite_from(self, actor):
        """
            Checks if the activity is already favorited by this actor
        """
        actor_favorited = [like_actor for like_actor in self.get('favorites', []) if like_actor.get(actor.unique, None) == actor[actor.unique]]
        return True if actor_favorited else False
