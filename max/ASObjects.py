# -*- coding: utf-8 -*-
from max.MADObjects import MADDict
from max.utils.formatting import findHashtags
from max.utils.formatting import findKeywords
from max.utils.formatting import formatMessageEntities

from max.security import Manager, Owner, is_owner
from max.security.permissions import delete_comment
from pyramid.security import Allow
from pyramid.decorator import reify
from max.utils.dicts import deepcopy
from hashlib import sha1


class ASObject(MADDict):
    """
        Base Class for objects determining Activity types,
        provides the base for validating the object by subclassing it
        and specifing an schema with required values
    """
    data = {}
    schema = {}
    objectType = ''

    def __init__(self, request, data, creating=True):
        """
        """
        self.request = request
        self.data = data
        if creating:
            self.processFields()
        self.update(self.data)


class Note(ASObject):
    """
        An activitystrea.ms Note Object
    """
    data = {}
    objectType = 'Note'
    schema = {
        '_id': {},
        'content': {
            'required': 1,
            'formatters': ['stripHTMLTags']
        },
        'objectType': {
            'required': 1
        },
        '_hashtags': {},
        '_keywords': {},
    }

    def __init__(self, request, data, creating=True):
        """
        """
        self.request = request
        self.creating = creating
        self.data = data
        if creating:
            self.processFields()
            self.data['content'] = formatMessageEntities(request, self.data.get('content', ''))
            hashtags = findHashtags(self.data['content'])
            if hashtags:
                self.data['_hashtags'] = hashtags
            self.setKeywords()
        self.update(self.data)

    def setKeywords(self):
        self['_keywords'] = findKeywords(self.data['content'])


class Comment(ASObject):
    """
        An activitystrea.ms Comment Object
    """
    data = {}
    objectType = 'Comment'
    schema = {
        'actor': {},
        '_id': {},
        'content': {
            'required': 1,
            'formatters': ['stripHTMLTags']
        },
        'objectType': {
            'required': 1
        },
        'inReplyTo': {
            'required': 1
        },
        '_hashtags': {},
        '_keywords': {},
    }

    def __init__(self, request, data, creating=True):
        """
        """
        self.request = request
        self.creating = creating
        self.data = data
        if creating:
            self.processFields()
            self.data['content'] = formatMessageEntities(self.request, self.data.get('content', ''))
            hashtags = findHashtags(self.data['content'])
            if hashtags:
                self.data['_hashtags'] = hashtags
            self.setKeywords()
        else:
            existing_id = self.data.pop('id', None)
            if existing_id:
                self.data['_id'] = existing_id

        self.update(self.data)

    def delete(self):
        """
            Proxy of the comment's activity delete_comment
        """
        self.__parent__.activity.delete_comment(self['_id'])

    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, delete_comment),
            (Allow, Owner, delete_comment),
        ]
        activity = self.__parent__.activity

        # If the user accessing the activity owns it, give it permission to delete
        if is_owner(activity, activity.request.authenticated_userid):
            acl.append((Allow, activity.request.authenticated_userid, delete_comment))

        if activity.get('contexts', []) and hasattr(activity.request.actor, 'getSubscription'):
            subscription = activity.request.actor.getSubscription(activity.contexts[0])
            if subscription:
                permissions = subscription.get('permissions', [])
                if 'delete' in permissions:
                    acl.append((Allow, activity.request.authenticated_userid, delete_comment))

        return acl

    @property
    def _owner(self):
        """
            XXX Try to improve this ...

            This wraps the actor username that posted the comment as _owner, to be able to check
            ownership when using a Comment as a traversed object
        """
        return self.get('actor', {}).get('username', None)

    def setKeywords(self):
        self['_keywords'] = findKeywords(self.data['content'])


class Conversation(ASObject):
    """
        An Max Context Object
    """
    data = {}
    objectType = 'Conversation'
    schema = {
        'id': {},
        'objectType': {
            'required': 1
        },
        'participants': {
            'required': 1
        },
    }


class Context(ASObject):
    """
        An Max Context Object
    """
    data = {}
    objectType = 'Context'
    schema = {
        '_id': {},
        'url': {
            'required': 1
        },
        'objectType': {
            'required': 1
        },
    }

    def getHash(self):
        """
            Calculates the hash based on the url
        """
        return sha1(self.url).hexdigest()


class Person(ASObject):
    """
        An Max Context Object
    """
    data = {}
    objectType = 'Person'
    schema = {
        '_id': {},
        'username': {
            'required': 1
        },
        'displayName': {
            'required': 0
        },
        'objectType': {
            'required': 1
        },
    }


class Activity(ASObject):
    """
        An Max Activity Object
    """
    data = {}
    objectType = 'Activity'
    schema = {
        '_id': {},
        'objectType': {
            'required': 1
        },
        'likes': {},
        'liked': {},
        'likesCount': {},
        'favorites': {},
        'favorited': {},
        'favoritesCount': {},
    }


class File(Note):
    """
        An activitystrea.ms File Object
    """

    def __init__(self, request, data, creating=True):
        """
        """
        self.request = request
        self.data = data
        self.processFields()
        self.update(data)

    objectType = 'File'
    schema = deepcopy(Note.schema)
    schema['content']['required'] = 0
    schema['file'] = {}
    schema['filename'] = {}
    schema['mimetype'] = {}
    schema['fullURL'] = {}


class Image(File):
    """
        An activitystrea.ms Image Object
    """
    objectType = 'Image'
    schema = deepcopy(File.schema)
    schema['thumbURL'] = {}
