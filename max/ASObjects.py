from max.rest.utils import formatMessageEntities, findHashtags, findKeywords
from max.MADObjects import MADDict


class ASObject(MADDict):
    """
        Base Class for objects determining Activity types,
        provides the base for validating the object by subclassing it
        and specifing an schema with required values
    """
    data = {}
    schema = {}
    objectType = ''

    def __init__(self, data):
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
    schema = {
                '_id':           dict(),
                'content':       dict(required=1),
                'objectType':    dict(required=1),
                '_hashtags':     dict(),
                '_keywords':     dict(),
             }

    def __init__(self, data):
        """
        """
        self.data = data
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
    schema = {
                '_id':         dict(),
                'content':     dict(required=1),
                'objectType':  dict(required=1),
                'inReplyTo':   dict(required=1),
                '_hashtags':     dict(),
                '_keywords':     dict(),
             }

    def __init__(self, data):
        """
        """
        self.data = data
        self.processFields()
        self.data['content'] = formatMessageEntities(self.data['content'])
        hashtags = findHashtags(self.data['content'])
        if hashtags:
            self.data['_hashtags'] = hashtags
        self.data['_keywords'] = findKeywords(self.data['content'])
        self.update(self.data)


class Uri(ASObject):
    """
        An Max Context Object
    """
    data = {}
    objectType = 'Uri '
    schema = {
                '_id':         dict(),
                'url':         dict(required=1),
                'objectType':  dict(required=1),
             }

    def __init__(self, data):
        """
        """
        self.data = data
        self.processFields()
        self.update(data)


class Person(ASObject):
    """
        An Max Context Object
    """
    data = {}
    objectType = 'Person'
    schema = {
                '_id':         dict(),
                'username':    dict(required=1),
                'displayName': dict(required=0),
                'objectType':  dict(required=1),
             }

    def __init__(self, data):
        """
        """
        self.data = data
        self.processFields()
        self.update(data)
