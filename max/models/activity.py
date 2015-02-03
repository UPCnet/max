# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.MADObjects import MADBase
from max.exceptions import Unauthorized
from max.models.context import Context
from max.models.user import User
from max.rabbitmq import RabbitNotifications
from max.rest.utils import canWriteInContexts
from max.rest.utils import getMaxModelByObjectType
from max.rest.utils import hasPermission
from max.rest.utils import rfc3339_parse
from max.rest.utils import rotate_image_by_EXIF

from PIL import Image
from bson import ObjectId
from hashlib import sha1

import datetime
import json
import os
import re
import requests


class BaseActivity(MADBase):
    """
        An activitystrea.ms Activity object representation
    """
    unique = '_id'
    schema = {
        '_id': {},
        '_creator': {},
        '_owner': {},
        '_keywords': {
            'default': []
        },
        'objectType': {
            'default': 'activity'
        },
        'actor': {
            'required': 1
        },
        'verb': {
            'required': 1
        },
        'object': {
            'required': 1
        },
        'published': {},
        '_created': {},
        'lastComment': {},
        'contexts': {},
        'replies': {
            'default': []
        },
        'generator': {
            'default': None
        },
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

        # Set date if specified
        if 'published' in self.data:
            self._created = self.published
            self.published = rfc3339_parse(self.data['published'])

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

        notify = self.get('contexts', [{}])[0].get('notifications', False)
        if notify in ['comments']:
            notifier = RabbitNotifications(self.request)
            notifier.notify_context_activity_comment(self, comment)

    def delete_comment(self, commentid):
        """
        """
        self.delete_from_list('replies', {'id': commentid})
        self.replies = [comment for comment in self.replies if comment['id'] != commentid]
        self.setKeywords()
        self.save()
        # XXX TODO Update hastags

    def extract_file_from_activity(self):
        file_activity = self['object']['file']
        del self['object']['file']
        return file_activity

    def getBlob(self, extension=''):
        """
        """
        base_path = self.request.registry.settings.get('file_repository')
        separator = '.' if extension else ''

        dirs = list(re.search('(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{12})', str(self._id)).groups())
        filename = dirs.pop() + separator + extension

        path = base_path + '/' + '/'.join(dirs)

        if os.path.exists(os.path.join(path, filename)):
            data = open(os.path.join(path, filename)).read()
            return data
        return None

    def getFile(self):
        """
            Gets the image associated to this message, if the message is of type file
            And the image exists
        """
        if self.object['objectType'] != 'file':
            return None

        collection_item_storage = self.context_class.user_subscription_storage
        collection_item_key = self.context_class.unique.lstrip('_')

        if self.get('contexts', []):
            readable_contexts_urls = [a[collection_item_key] for a in self.request.actor[collection_item_storage] if 'read' in a['permissions']]

            can_read = False
            for context in self['contexts']:
                if context[collection_item_key] in readable_contexts_urls:
                    can_read = True
        else:
            # Sure ??? Do we have to check if the activity is ours, or from a followed user?
            # Try to unify this criteria with the criteria used in geting the timeline activities
            can_read = True

        if not can_read:
            raise Unauthorized("You are not allowed to read this activity: %s" % str(self._id))

        image_file = self.getBlob()

        if image_file is None:
            return None, None
        else:
            return image_file, str(self['object'].get('mimetype', 'application/octet-stream'))

    def getImage(self, size):
        """
            Gets the image associated to this message, if the message is of type image
            And the image exists
        """
        if self.object['objectType'] != 'image':
            return None

        collection_item_storage = self.context_class.user_subscription_storage
        collection_item_key = self.context_class.unique.lstrip('_')

        file_extension = size if size != 'full' else ''

        if self.get('contexts', []):
            readable_contexts_urls = [a[collection_item_key] for a in self.request.actor[collection_item_storage] if 'read' in a['permissions']]

            can_read = False
            for context in self['contexts']:
                if context[collection_item_key] in readable_contexts_urls:
                    can_read = True
        else:
            # Sure ??? Do we have to check if the activity is ours, or from a followed user?
            # Try to unify this criteria with the criteria used in geting the timeline activities
            can_read = True

        if not can_read:
            raise Unauthorized("You are not allowed to read this activity: %s" % str(self._id))

        image_file = self.getBlob(extension=file_extension)

        if image_file is None:
            return None, None
        else:

            content_type = 'image/jpeg' if size != 'full' else str(self['object'].get('mimetype', 'image/jpeg'))
            return image_file, content_type

    def process_file(self, request, activity_file):
        """
            Process file and save it into the database
        """
        base_path = request.registry.settings.get('file_repository')
        uploadURL = ''
        file_type = self['object'].get('objectType', 'file').lower()
        # Look if the activity belongs to an specific context
        if self.get('contexts', False):
            # Look if we need to upload to an external URL
            if self.get('contexts')[0]['objectType'] == 'context':
                context = getMaxModelByObjectType(self.get('contexts')[0]['objectType'])()
                context.fromDatabase(self.get('contexts')[0]['hash'])
                uploadURL = context.get('uploadURL', '')
            else:
                context = getMaxModelByObjectType(self.get('contexts')[0]['objectType'])()
                context.fromDatabase(ObjectId(self.get('contexts')[0]['id']))
                uploadURL = context.get('uploadURL', '')

        if uploadURL:
            headers = {'X-Oauth-Scope': request.headers.get('X-Oauth-Scope'),
                       'X-Oauth-Username': request.headers.get('X-Oauth-Username'),
                       'X-Oauth-Token': request.headers.get('X-Oauth-Token')
                       }
            # Todo: Make sure that the mimetype is correctly or even informed
            # Use magic or imghdr libraries for that
            files = {'image': (activity_file.filename, activity_file.file, activity_file.type)}
            res = requests.post(uploadURL, headers=headers, files=files)
            if res.status_code == 201:
                response = json.loads(res.text)
                self['object']['fullURL'] = response.get('uploadURL', '')
                if file_type == 'image':
                    self['object']['thumbURL'] = response.get('thumbURL', '')

        else:
            # We have a conversation or an activity with no related context
            # or a context with no community which we should save localy
            dirs = list(re.search('(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{12})', str(self['_id'])).groups())
            filename = dirs.pop()
            path = base_path + '/' + '/'.join(dirs)
            if not os.path.exists(path):
                os.makedirs(path)
            r_file = open(path + '/' + filename, 'w')
            r_file.write(activity_file.file.read())
            r_file.close()

            full_endpoint_name = 'image/full' if file_type == 'image' else 'file/download'
            self['object']['fullURL'] = '/{}/{}/{}'.format(self.resource_root, str(self['_id']), full_endpoint_name)

            if file_type == 'image':
                # Generate thumbnail
                activity_file.file.seek(0)
                image = Image.open(activity_file.file)
                thumb = rotate_image_by_EXIF(image)
                thumb.thumbnail((400, 400), Image.ANTIALIAS)
                thumb.save(path + '/' + filename + ".thumb", "JPEG")

                self['object']['thumbURL'] = '/{}/{}/image/thumb'.format(self.resource_root, str(self['_id']))
        self['object']['mimetype'] = activity_file.headers.getheader('content-type', '')

        # If there's a user-provided filename, preserve it
        if 'filename' not in self['object']:
            # Try to get filename from content disposition
            filename = re.search(r'filename="(.*?)"', activity_file.headers.getheader('content-disposition', '')).groups()
            # Ignore empty filenames and "file" filenames (the latter coming from maxclient)
            if filename and filename != 'file':
                self['object']['filename'] = filename[0]


class Activity(BaseActivity):
    """
        An activity
    """
    collection = 'activity'
    context_collection = 'contexts'
    context_class = Context
    resource_root = 'activities'
    unique = '_id'
    schema = dict(BaseActivity.schema)
    schema['deletable'] = {}
    schema['liked'] = {}
    schema['favorited'] = {}
    schema['flagged'] = {}
    schema['likes'] = {'default': []}
    schema['likesCount'] = {'default': 0}
    schema['lastLike'] = {}
    schema['favorites'] = {'default': []}
    schema['favoritesCount'] = {'default': 0}

    def _on_saving_object(self, oid):
        if not hasattr(self, 'lastComment'):
            self.lastComment = oid
            self.save()

    def _on_insert_object(self, oid):
        # notify activity if the activity is from a context
        # with enabled notifications

        notify = self.get('contexts', [{}])[0].get('notifications', False)
        if notify in ['posts', 'comments', True]:
            notifier = RabbitNotifications(self.request)
            notifier.notify_context_activity(self)

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

    def flag(self):
        """
        """
        self.flagged = datetime.datetime.utcnow()

    def unflag(self):
        """
        """
        self.flagged = None

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
        self.lastLike = datetime.datetime.utcnow()
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
