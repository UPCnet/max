# -*- coding: utf-8 -*-
from max.MADObjects import MADDict
from max.rest.utils import findHashtags
from max.rest.utils import findKeywords
from max.rest.utils import formatMessageEntities

from copy import deepcopy
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

    def __init__(self, data, creating=True):
        """
        """
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

    def __init__(self, data, creating=True):
        """
        """
        self.creating = creating
        self.data = data
        if creating:
            self.processFields()
            self.data['content'] = formatMessageEntities(self.data.get('content', ''))
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

    def __init__(self, data, creating=True):
        """
        """
        self.creating = creating
        self.data = data
        if creating:
            self.processFields()
            self.data['content'] = formatMessageEntities(self.data.get('content', ''))
            hashtags = findHashtags(self.data['content'])
            if hashtags:
                self.data['_hashtags'] = hashtags
            self.setKeywords()
        self.update(self.data)

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

    def __init__(self, data, creating=True):
        """
        """
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
