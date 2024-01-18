# -*- coding: utf-8 -*-
from max import DEFAULT_CONTEXT_PERMISSIONS
from max.MADObjects import MADBase
from max.models.context import Context
from max.models.user import User
from max.rabbitmq import RabbitNotifications
from max.resources import CommentsTraverser
from max.security import Manager
from max.security import Owner
from max.security import is_owner
from max.security import is_self_operation
from max.security.permissions import add_comment
from max.security.permissions import delete_activity
from max.security.permissions import delete_comment
from max.security.permissions import favorite
from max.security.permissions import flag
from max.security.permissions import like
from max.security.permissions import list_comments
from max.security.permissions import modify_activity
from max.security.permissions import unfavorite
from max.security.permissions import unflag
from max.security.permissions import unlike
from max.security.permissions import view_activity
from max.utils import getMaxModelByObjectType
from max.utils import hasPermission
from max.utils.dates import rfc3339_parse
from max.utils.image import rotate_image_by_EXIF

from pyramid.decorator import reify
from pyramid.security import Allow
from pyramid.security import Authenticated

from PIL import Image
from bson import ObjectId

import datetime
import json
import os
import re
import requests

ACTIVITY_CONTEXT_FIELDS = ['displayName', 'tags', 'hash', 'url', 'objectType', 'notifications']


class BaseActivity(MADBase):
    """
        An activitystrea.ms Activity object representation
    """
    default_field_view_permission = view_activity
    default_field_edit_permission = modify_activity
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
        isPerson = self.data['actor']['objectType'] == 'person'
        isContext = self.data['actor']['objectType'] == 'context'

        if isPerson:
            return request.actor['username']
        elif isContext:
            return request.authenticated_userid

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
        subobject = wrapper(self.request, self.data['object'])
        ob['object'] = subobject

        if 'contexts' in self.data:
            ob['contexts'] = [self.data['contexts'][0].flatten(preserve=ACTIVITY_CONTEXT_FIELDS), ]

        self.update(ob)

        # Set date if specified
        if 'published' in self.data:
            self._created = self['published']
            self['published'] = rfc3339_parse(self.data['published'])

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

        if self['verb'] in ['post']:
            self.setKeywords()

    def modifyActivity(self, properties):
        """Update the Activity object with the given properties"""

        self.updateFields(properties)
        self.save()

    def get_comment(self, commentid):
        comments = [comment for comment in self['replies'] if comment['id'] == commentid]
        return comments[0] if comments is not [] else False

    def setKeywords(self):
        # Append actor as username if object has keywords and actor is a Person
        self['_keywords'] = []
        self['_keywords'].extend(self['object'].get('_keywords', []))
        if self['actor']['objectType'] == 'person':
            self['_keywords'].append(self['actor']['username'])
            self['_keywords'].extend(self['actor']['username'].split('.'))
            self['_keywords'].extend(self['actor'].get('displayName', '').lower().split())

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

        # Clean innecessary fields
        non_needed_actor_fields = ['talkingIn', 'subscribedTo', 'following', 'last_login', '_id', 'published', 'twitterUsername']
        for fieldname in non_needed_actor_fields:
            if fieldname in comment['actor']:
                del comment['actor'][fieldname]

        self.add_to_list('replies', comment, allow_duplicates=True)
        self.setKeywords()

        activity_hashtags = self['object'].setdefault('_hashtags', [])
        activity_hashtags.extend(comment.get('_hashtags', []))
        self['object']['_hashtags'] = list(set(activity_hashtags))
        self['lastComment'] = ObjectId(comment['id'])

        self.save()

        # Modificamos el comportamiento de la notificación push de comentarios.
        # Hasta ahora si cuando creas la actividad tienes marcado el que notifique las push de actividad y comentario,
        # todos los comentarios que hagas de esa actividad se envía la notificación push aunque luego lo desactives
        # y al contrario, si cuando creas la actividad no esta marcado que notifique las push, aunque lo actives no lo notifica.

        # Ahora miramos la comunidad para ver si esta activado o no para enviar la notificación push.
        contexts = self.mdb_collection.database.contexts.find({'hash': self.get("contexts")[0]['hash']})
        for context in contexts:
            notify = context.get('notifications', False)

        #notify = self.get('contexts', [{}])[0].get('notifications', False)
        if notify in ['comments']:
            notifier = RabbitNotifications(self.request)
            notifier.notify_context_activity_comment(self, comment)

    def delete_comment(self, commentid):
        """
        """
        self.delete_from_list('replies', {'id': commentid})
        self['replies'] = [comment for comment in self['replies'] if comment.get('id', comment.get('_id')) != commentid]
        if self['replies'] == []:
            self['lastComment'] = self['_id']
        else:
            self['lastComment'] = ObjectId(str(self['replies'][-1]['id']))

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

        dirs = list(re.search('(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{12})', str(self['_id'])).groups())
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
        if self['object']['objectType'] != 'file':
            return None

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
        if self['object']['objectType'] != 'image':
            return None

        file_extension = size if size != 'full' else ''

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
            context = self.get('contexts')[0]
            ContextClass = getMaxModelByObjectType(self.get('contexts')[0]['objectType'])
            identifier = context[ContextClass.unique] if ContextClass.unique in context else context[ContextClass.unique.lstrip('_')]
            context = ContextClass.from_database(self.request, identifier)
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
            try:
                r_file.write(activity_file.file.read())
            except:
                from base64 import decodestring
                r_file.write(decodestring(activity_file.file))
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
    schema['comments'] = {}
    schema['liked'] = {}
    schema['favorited'] = {}
    schema['flagged'] = {}
    schema['likes'] = {'default': []}
    schema['likesCount'] = {'default': 0}
    schema['lastLike'] = {}
    schema['favorites'] = {'default': []}
    schema['favoritesCount'] = {'default': 0}

    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, view_activity),
            (Allow, Manager, delete_activity),
            (Allow, Manager, list_comments),
            (Allow, Manager, add_comment),
            (Allow, Manager, favorite),
            (Allow, Manager, unfavorite),
            (Allow, Manager, like),

            (Allow, Owner, view_activity),
            (Allow, Owner, delete_activity),

        ]
        if is_self_operation(self.request):
            acl.append((Allow, self.request.authenticated_userid, favorite))

            if self.has_favorite_from(self.request.actor):
                acl.append((Allow, self.request.authenticated_userid, unfavorite))

        # When checking permissions directly on the object (For example when determining
        # the visible fields), request.context.owner will be related to the owner of where we are posting the
        # activity, for example, when posting to a context, the context), so we need to provide permissions
        # for the owner of the object itself, or the flatten will result empty...
        if is_owner(self, self.request.authenticated_userid):
            acl.append((Allow, self.request.authenticated_userid, view_activity))

        # If we have an activity that has contexts, grant view_activity if the context
        # subscription provides the read permission.
        #
        # There's two use case where the actor's that just posted the activity may not have a subscription.
        #  1. A Manager is posting in a context as himself (not impersonating) and he's not subscribed.
        #     As we allow this in static acls, a manager will already have the permissions granted below.
        #  2. A Manager is posting in a context as a context, so the context won't be subcribed in any way.
        #     As the user authenticated wil be a manager, it will already have the permissions granted below.

        if self.get('contexts', []) and hasattr(self.request.actor, 'getSubscription'):
            from max.models import Context

            # When dealing with context activities, request context will be already loaded, so reuse it
            activity_context_same_as_request_context = isinstance(self.request.context, Context) and self.request.context['hash'] == self['contexts'][0]['hash']
            if activity_context_same_as_request_context:
                context = self.request.context
            else:
                # When activity context is not loaded, instantiate a lazy one
                context = Context.from_object(self.request, self['contexts'][0])

            subscription = self.request.actor.getSubscription(context)
            if subscription:
                permissions = subscription.get('permissions', [])
                if 'read' in permissions:
                    acl.append((Allow, self.request.authenticated_userid, view_activity))
                    acl.append((Allow, self.request.authenticated_userid, list_comments))

                    # Allow like on non impersonated requests
                    if is_self_operation(self.request):
                        acl.append((Allow, self.request.authenticated_userid, like))

                if 'flag' in permissions:
                    acl.append((Allow, self.request.authenticated_userid, flag))
                    acl.append((Allow, self.request.authenticated_userid, unflag))

                if 'delete' in permissions:
                    acl.append((Allow, self.request.authenticated_userid, delete_activity))
                    acl.append((Allow, self.request.authenticated_userid, delete_comment))

                if 'write' in permissions:
                    acl.append((Allow, self.request.authenticated_userid, add_comment))

            # If no susbcription found, check context policy
            else:
                # XXX This should be cached at resource level
                context.wake()
                if context.get('permissions', {}).get('read', DEFAULT_CONTEXT_PERMISSIONS['read']) == 'public':
                    acl.append((Allow, self.request.authenticated_userid, view_activity))
                    if is_self_operation(self.request):
                        acl.append((Allow, self.request.authenticated_userid, like))

            # Only context activites can be flagged/unflagged, so we give permissions to
            # Manager here, as it don't make sense to do it globally
            acl.extend([
                (Allow, Manager, flag),
                (Allow, Manager, unflag)
            ])

        # Activies without a context are considered public to all authenticated users, so commentable.
        # Those activities commments also will be readable by all authenticated users.
        # Owners of activities can delete them outside contexts.
        else:
            acl.extend([
                (Allow, Authenticated, view_activity),
                (Allow, Authenticated, add_comment),
                (Allow, Owner, delete_comment),
                (Allow, Authenticated, list_comments),
            ])
            if is_self_operation(self.request):
                acl.append((Allow, self.request.authenticated_userid, like))

        # Allow unlike only if actor has a like on this activity.
        # Allow Managers to unlike likes from other users
        if self.has_like_from(self.request.actor):
            acl.append((Allow, Manager, unlike))
            if is_self_operation(self.request):
                acl.append((Allow, self.request.authenticated_userid, unlike))

        return acl

    def flatten(self, *args, **kwargs):
        self.pop('comments', None)
        return super(Activity, self).flatten(*args, **kwargs)

    def _before_saving_object(self):
        # Remove comments traverser before saving
        self.pop('comments', None)

    def _before_insert_object(self):
        # Remove comments traverser before inserting
        self.pop('comments', None)

    def _after_insert_object(self, oid):
        # notify activity if the activity is from a context
        # with enabled notifications
        self['lastComment'] = oid
        self.save()

        notify = self.get('contexts', [{}])[0].get('notifications', False)
        if notify in ['posts', 'comments', True]:
            notifier = RabbitNotifications(self.request)
            notifier.notify_context_activity(self)

    def _post_init_from_object(self, source):
        """
            * Set the deletable flag on the object. If user is the owner don't check anything else,
            otherwhise, check if user has permissions to delete activities on that context

            * Set the liked and favorited flags on the object, with the number of each marks
        """
        if isinstance(self.request.actor, User):
            actor_id_field = 'username'
        else:
            actor_id_field = 'url'
        self['deletable'] = self.request.actor[actor_id_field] == self['_owner']
        if not self['deletable'] and self.get('contexts'):
            subscriptions_with_delete_permission = [subscription['hash'] for subscription in self.request.actor.get('subscribedTo', []) if hasPermission(subscription, 'delete')]
            for context in self.get('contexts'):
                self['deletable'] = context['hash'] in subscriptions_with_delete_permission

        # Mark the comments with the deletable flag too
        for comment in self.get('replies', []):
            comment['deletable'] = self['deletable'] or self.request.actor[actor_id_field] == comment['actor']['username']

        self['favorited'] = self.has_favorite_from(self.request.actor)
        self['liked'] = self.has_like_from(self.request.actor)

        self['comments'] = CommentsTraverser(None, self.request, self)

    def flag(self):
        """
        """
        self['flagged'] = datetime.datetime.utcnow()

    def unflag(self):
        """
        """
        self['flagged'] = None

    def add_favorite_from(self, actor):
        """
            Adds a favorite mark from somebody to an activity
        """
        prepared_actor = {
            actor.unique: actor.get(actor.unique),
            'objectType': actor['objectType']
        }
        self.add_to_list('favorites', prepared_actor, allow_duplicates=False)
        self['favoritesCount'] = len(self['favorites'])
        self.save()

    def add_like_from(self, actor):
        """
            Adds a like mark from somebody to an activity
        """
        prepared_actor = {
            actor.unique: actor.get(actor.unique),
            'objectType': actor['objectType']
        }
        self.add_to_list('likes', prepared_actor, allow_duplicates=False)
        self['likesCount'] = len(self['likes'])
        self['lastLike'] = datetime.datetime.utcnow()
        self.save()

    def delete_favorite_from(self, actor):
        """
            Deletes the favorite mark from somebody from an activity
        """
        self.delete_from_list('favorites', {actor.unique: actor.get(actor.unique)})
        self['favorites'] = [favorite for favorite in self['favorites'] if favorite[actor.unique] != actor[actor.unique]]
        self['favoritesCount'] = len(self['favorites'])
        self.save()

    def delete_like_from(self, actor):
        """
            Deletes the like mark from somebody from an activity
        """
        self.delete_from_list('likes', {actor.unique: actor.get(actor.unique)})
        self['likes'] = [like for like in self['likes'] if like[actor.unique] != actor[actor.unique]]
        self['likesCount'] = len(self['likes'])
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
