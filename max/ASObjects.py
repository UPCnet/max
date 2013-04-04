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
              'content':       dict(required=1),
              'objectType':    dict(required=1),
              '_hashtags':     dict(),
              '_keywords':     dict(),
              }

    def __init__(self, data, creating=True):
        """
        """
        self.data = data
        if creating:
            self.processFields()
            self.data['content'] = formatMessageEntities(self.data['content'])
            hashtags = findHashtags(self.data['content'])
            if hashtags:
                self.data['_hashtags'] = hashtags
            self.data['_keywords'] = findKeywords(self.data['content'])
        self.update(self.data)


class Message(ASObject):
    """
        An activitystrea.ms Note Object
    """
    data = {}
    objectType = 'Message'
    schema = {'_id':           dict(),
              'content':       dict(required=1),
              'objectType':    dict(required=1),
              '_hashtags':     dict(),
              '_keywords':     dict(),
              }

    def __init__(self, data, creating=True):
        """
        """
        self.data = data
        if creating:
            self.processFields()
            self.data['content'] = formatMessageEntities(self.data['content'])
            hashtags = findHashtags(self.data['content'])
            if hashtags:
                self.data['_hashtags'] = hashtags
            self.data['_keywords'] = findKeywords(self.data['content'])
        self.update(self.data)


class Comment(ASObject):
    """
        An activitystrea.ms Comment Object
    """
    data = {}
    objectType = 'Comment'
    schema = {'_id':         dict(),
              'content':     dict(required=1),
              'objectType':  dict(required=1),
              'inReplyTo':   dict(required=1),
              '_hashtags':     dict(),
              '_keywords':     dict(),
              }

    def __init__(self, data, creating=True):
        """
        """
        self.data = data
        if creating:
            self.processFields()
            self.data['content'] = formatMessageEntities(self.data['content'])
            hashtags = findHashtags(self.data['content'])
            if hashtags:
                self.data['_hashtags'] = hashtags
            self.data['_keywords'] = findKeywords(self.data['content'])
        self.update(self.data)


class Conversation(ASObject):
    """
        An Max Context Object
    """
    data = {}
    objectType = 'Conversation'
    schema = {'_id':          dict(),
              'objectType':   dict(required=1),
              'participants': dict(required=1),
              '_hash':        dict(required=0)
              }

    def __init__(self, data, creating=True):
        """
        """
        self.data = data
        self.processFields()
        self.update(data)
        self.getHash()

    def getHash(self):
        """
            Calculates the hash based on the participants of the conversation
            and the creation date. Return the existing hash if already set
        """
        if self.get('_hash', None) is None:
            participants = list(self.participants)  # Make a copy
            participants.sort()                     # Sort it
            alltogether = ''.join(participants)     # Join It
            date = rfc3339(datetime.now(), utc=True, use_system_timezone=False)
            alltogether += date
            self._hash = sha1(alltogether).hexdigest()  # Hash it
        return self._hash

    def getDisplayName(self):
        return ', '.join(self.participants)


class Context(ASObject):
    """
        An Max Context Object
    """
    data = {}
    objectType = 'Uri'
    schema = {'_id':         dict(),
              'url':         dict(required=1),
              'objectType':  dict(required=1),
              }

    def __init__(self, data, creating=True):
        """
        """
        self.data = data
        self.processFields()
        self.update(data)

    def getHash(self):
        """
            Calculates the hash based on the url
        """
        return sha1(self.url).hexdigest()

    def getDisplayName(self):
        return self.url


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

    def __init__(self, data, creating=True):
        """
        """
        self.data = data
        self.processFields()
        self.update(data)
