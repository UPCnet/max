# -*- coding: utf-8 -*-
from max.rest.utils import formatMessageEntities, findHashtags, findKeywords
from max.MADObjects import MADDict
from hashlib import sha1
from datetime import datetime
from rfc3339 import rfc3339


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
        self.processFields()
        self.update(data)


class Note(ASObject):
    """
        An activitystrea.ms Note Object
    """
    data = {}
    objectType = 'Note'
    schema = {'_id':           dict(),
              'content':       dict(required=1, formatters=['stripHTMLTags']),
              'objectType':    dict(required=1),
              '_hashtags':     dict(),
              '_keywords':     dict(),
              }

    def __init__(self, data, creating=True):
        """
        """
        self.creating = creating
        self.data = data
        if creating:
            self.processFields()
            self.data['content'] = formatMessageEntities(self.data['content'])
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
    schema = {'_id':         dict(),
              'content':     dict(required=1, formatters=['stripHTMLTags']),
              'objectType':  dict(required=1),
              'inReplyTo':   dict(required=1),
              '_hashtags':     dict(),
              '_keywords':     dict(),
              }

    def __init__(self, data, creating=True):
        """
        """
        self.creating = creating
        self.data = data
        if creating:
            self.processFields()
            self.data['content'] = formatMessageEntities(self.data['content'])
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
    schema = {'id':          dict(),
              'objectType':   dict(required=1),
              'participants': dict(required=1),
              }


class Context(ASObject):
    """
        An Max Context Object
    """
    data = {}
    objectType = 'Context'
    schema = {'_id':         dict(),
              'url':         dict(required=1),
              'objectType':  dict(required=1),
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
    schema = {'_id':         dict(),
              'username':    dict(required=1),
              'displayName': dict(required=0),
              'objectType':  dict(required=1),
              }


class Activity(ASObject):
    """
        An Max Activity Object
    """
    data = {}
    objectType = 'Activity'
    schema = {'_id':         dict(),
              'objectType':  dict(required=1),
              'likes':       dict(),
              'liked':       dict(),
              'likesCount':  dict(),
              'favorites':   dict(),
              'favorited':   dict(),
              'favoritesCount':  dict()
              }