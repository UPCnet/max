
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
                '_id':         dict(required=0),
                'content':     dict(required=0,request=1),
                'objectType':  dict(required=0,request=1),
             }

    def __init__(self,data):
        """
        """
        self.data = data
        self.validate()
        self.update(data)


class Comment(ASObject):
    """
        An activitystrea.ms Comment Object
    """
    data = {}
    schema = {
                '_id':         dict(required=0),
                'content':     dict(required=0,request=1),
                'objectType':  dict(required=0,request=1),
                'inReplyTo':   dict(required=0,request=1),
             }

    def __init__(self,data):
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
                '_id':         dict(required=0),
                'url':         dict(required=0,request=1),
                'objectType':  dict(required=0,request=1),
             }

    def __init__(self,data):
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
                '_id':         dict(required=0),
                'displayName': dict(required=0,request=1),
                'objectType':  dict(required=0,request=1),
             }

    def __init__(self,data):
        """
        """
        self.data = data
        self.validate()
        self.update(data)
