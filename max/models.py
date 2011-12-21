import time
from rfc3339 import rfc3339
from max.rest.utils import extractPostData, flatten, RUDict
from max.exceptions import MissingField
import datetime
from pyramid.request import Request
from pymongo.objectid import ObjectId

class MADDict(dict):
    """
        A simple vitaminated dict for holding a MongoBD arbitrary object
    """
    schema = {}    

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        return val

    def __setitem__(self, key, val):
        """
            Allow only fields defined in schema to be inserted in the dict
            ignore non schema values
        """
        if key in self.schema.keys():
            dict.__setitem__(self, key, val)
        else:
            pass

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).iteritems():
            self[k] = v

    def __setattr__(self, key, value):
        """
            Enables setting values of dict's items trough attribute assignment,
            while preserving default setting of class attributes
        """
        if hasattr(self, key):
            dict.__setattr__(self, key, value)
        else:
            self.__setitem__(key, value)

    def __getattr__(self, key):
        """
            Maps dict items access to attributes, while preserving access to class attributes
        """
        try:
            return self.__getattribute__(key)
        except AttributeError:
            return self.__getitem__(key)

    def checkParameterExists(self, fieldname):
        """
            Checks if a parameter 'fieldname' exists in the data dict, accepts fieldnames
            in the form object.subobject, in one level depth
        """

        parts = fieldname.split('.')

        base = self.data
        for part in parts:
            if part in base.keys():
                base = base[part]
            else:
                return False
        return True

    def validate(self):
        """
            Checks if all the required schema fields (request=1) are present in 
            the collected data
        """
        for fieldname in self.schema:
            if self.schema.get(fieldname).get('request', 0):
                if not self.checkParameterExists(fieldname):
                    raise MissingField(fieldname)
        return True        


class MADBase(MADDict):
    """
        Base Class for Objects in the MongoDB, It can be instantiated with a MongoDB Object
        or a request object in the source param.

        If instantiated with a MongoDB Object collection must be passed
        If instantiated with a request, rest_params may be passed to extend request params

        Provides the methods to validate and construct an object according to activitystrea.ms
        specifications by subclassing it and providing an schema with the required fields,
        and a structure builder function 'buildObject'
    """

    unique = ''
    collection = ''
    mdb_collection = None
    data = {}

    def __init__(self, source, collection=None, rest_params={}):
        """
        """
        if isinstance(source, Request):

            self.mdb_collection = source.context.db[self.collection]

            # self.data is a recursive dict, so we can "merge" dictionaries
            # with similar structure without losing keys
            # >>> dict1 = RUDict({'A': {'B':1}})
            # >>> dict2 = {'A': {'C':2}}
            # >>> dict1.update(dict2)
            # >>> dict1
            # {'A': {'B':1, C':2}}
            #

            self.data = RUDict({})
            self.data.update(extractPostData(source))
            self.data.update(rest_params)

            self.getActorFromDB()
            self.validate()

            #check if the object we pretend to create already exists
            existing_object = self.alreadyExists()
            if not existing_object:
                # if we are creating a new object, set the current date and build
                self['published'] = datetime.datetime.utcnow()
                self.buildObject()
            else:
                # if it's already on the DB, just populate with the object data
                self.update(existing_object)
        else:
            # if it's already on the DB, just populate with the object data
            # and set the collection
            self.mdb_collection = collection
            self.update(source)

    def getActorFromDB(self):
        """
            If a 'actor' object is present in the received params, search for the user
            record on the DB and set it as actor
        """
        if 'actor' in self.data:
            if '_id' not in self.data['actor'].keys():
                user_displayName = self.data['actor']['displayName']
                user = self.mdb_collection.database.users.find_one({'displayName': user_displayName})
                self.data['actor'] = user

    def insert(self):
        """
            Inserts the item into his defined collection and returns its _id
        """
        oid = self.mdb_collection.insert(self)
        return str(oid)

    def updateList(self,field,obj):
        """
            Updates an array field of a existing DB object appending the new obj
            and incrementing the totalItems counter
        """
        items = 'object.%s.items' % field
        count = 'object.%s.totalItems' % field
        self.mdb_collection.update({'_id':self['_id']},                                {
                                    '$push': {items: obj},
                                    '$inc': {count: 1}
                                })

    def alreadyExists(self):
        """
            Checks if there's an object with the value specified in the unique field.
            If present, return the object, otherwise returns None
        """
        unique = self.unique
        query = {unique: self.data.get(unique)}
        return self.mdb_collection.find_one(query)

    def flatten(self):
        """
            Recursively transforms non-json-serializable values and simplifies
            $oid and $data BISON structures. Intended for final output
        """
        dd = dict([(key, self[key]) for key in self.keys()])
        flatten(dd)
        return dd



    def getObjectWrapper(self,objType):
        """
            Get the aprpopiat class to be inserted in the object field
            of (mainly) an Activity
        """
        return {'comment':Comment,
                'note':Note,
               }[objType]

class ASObject(MADDict):
    """
        Base Class for objects determining Activity types,
        provides the base for validating the object by subclassing it
        and specifing an schema with required values
    """
    data = {}
    schema = {}
    
    def __init__(self,data):
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

class Activity(MADBase):
    """
        An activitystrea.ms Activity object representation
    """
    collection = 'activity'
    unique = '_id'
    schema = {
                '_id':         dict(required=0,request=0),
                'actor':       dict(required=0,request=1),
                'verb':        dict(required=0,request=1),
                'object':      dict(required=0,request=1),
                'published':   dict(required=0,request=0),
                'target':      dict(required=0,request=0),
             }

            
    def buildObject(self):
        """
            Updates the dict content with the activity structure,
            with data parsed from the request
        """
        ob = {'actor': {
                    'objectType': 'person',
                    '_id': self.data['actor']['_id'],
                    'displayName': self.data['actor']['displayName']
                    },
                'verb': 'post',
                'object': None, 
                }
        wrapper = self.getObjectWrapper(self.data['object']['objectType'])
        subobject = wrapper(self.data['object'])
        ob['object']=subobject

        if 'target' in self.data:
            ob['target'] = self.data['target']

        self.update(ob)

    def addComment(self,comment):
        """
            Adds a comment to an existing activity
        """
        self.updateList(self['_id'],comment)


class User(MADBase):
    """
        An activitystrea.ms User object representation
    """
    collection = 'users'
    unique = 'displayName'
    schema = {
                '_id':          dict(required=0),
                'displayName':  dict(required=1,request=1),
                'last_login':   dict(required=0),
                'following':    dict(required=0),
                'subscribedTo': dict(required=0),
                'published':    dict(required=0),
             }

    def buildObject(self):
        """
            Updates the dict content with the user structure,
            with data from the request
        """
        ob = {'displayName': self.data['displayName'],
                   'last_login': datetime.datetime.utcnow(),
                   'following': {'items': [], },
                   'subscribedTo': {'items': [], }
                   }
        self.update(ob)

