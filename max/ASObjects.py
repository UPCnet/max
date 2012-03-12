from max.rest.utils import formatMessageEntities, findHashtags
from max.MADObjects import MADDict


class ASObject(MADDict):
    """
        Base Class for objects determining Activity types,
        provides the base for validating the object by subclassing it
        and specifing an schema with required values
    """
    data = {}
    schema = {}

    def __init__(self, data):
        """
        """
        self.data = data
        self.validate()
        self.update(data)


class Note(ASObject):
    """
        An activitystrea.ms Note Object
    """
    data = {}
    schema = {
                '_id':         dict(),
                'content':     dict(required=1),
                'objectType':  dict(required=1),
             }

    def __init__(self, data):
        """
        """
        self.data = data
        self.validate()
        self.data['content'] = formatMessageEntities(self.data['content'])
        hashtags = findHashtags(self.data['content'])
        if hashtags:
            self.data['hashTags'] = hashtags
        self.update(data)


class Comment(ASObject):
    """
        An activitystrea.ms Comment Object
    """
    data = {}
    schema = {
                '_id':         dict(),
                'content':     dict(required=1),
                'objectType':  dict(required=1),
                'inReplyTo':   dict(required=1),
             }

    def __init__(self, data):
        """
        """
        self.data = data
        self.validate()
        self.update(data)


class Context(ASObject):
    """
        An Max Context Object
    """
    data = {}
    schema = {
                '_id':         dict(),
                'url':         dict(required=1),
                'objectType':  dict(required=1),
             }

    def __init__(self, data):
        """
        """
        self.data = data
        self.validate()
        self.update(data)


class Person(ASObject):
    """
        An Max Context Object
    """
    data = {}
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
        self.validate()
        self.update(data)
