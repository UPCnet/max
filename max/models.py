import time
from rfc3339 import rfc3339
from max.rest.utils import extractPostData, flatten
from max.exceptions import MissingField
import datetime
from pyramid.request import Request


class MADBase(dict):
    """A simple vitaminated dict for holding a MongoBD arbitrary object"""

    schema = {}
    unique = ''
    params = {}
    collection = ''
    mdb_collection = None
    data = {}

    def __init__(self, source, collection=None, rest_params={}):
        """
        """
        if isinstance(source, Request):

            self.mdb_collection = source.context.db[self.collection]
            self.data = extractPostData(source)
            self.data.update(rest_params)
            self.validate()
            existing_object = self.alreadyExists()
            if not existing_object:
                self['published'] = datetime.datetime.utcnow()
                self.buildObject()
            else:
                self.update(existing_object)
        else:
            self.mdb_collection = collection
            self.update(source)

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        return val

    def __setitem__(self, key, val):
        """
        Allow only fields defined in schema to be inserted in the dict
        """
        if key in self.schema.keys():
            dict.__setitem__(self, key, val)
        else:
            raise AttributeError

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
        return getattr(self, key, self.__getitem__(key))

    def insert(self):
        """
        Inserts the item into his defined collection and returns its _id
        """
        oid = self.mdb_collection.insert(self)
        return str(oid)

    def alreadyExists(self):
        """
        Checks if there's an object with the value specifiedin the unique field
        """
        unique = self.unique
        query = {unique: self.data.get(unique)}
        return self.mdb_collection.find_one(query)

    def flatten(self):
        """
        """
        dd = dict([(key, self[key]) for key in self.keys()])
        flatten(dd)
        return dd

    def checkParameterExists(self, fieldname):

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
        """
        for fieldname in self.params:
            if self.params.get(fieldname).get('required', 0):
                if not self.checkParameterExists(fieldname):
                    raise MissingField(fieldname)
        return True


class Activity(MADBase):
    """
    """
    collection = 'activity'
    unique = '_id'
    schema = {
                '_id':         dict(required=0),
                'actor':       dict(required=1),
                'verb':        dict(required=0),
                'object':      dict(required=0),
                'published':   dict(required=0),
                'target':      dict(required=0),
             }

    params = {
                'actor':             dict(required=1),
                'object.content':    dict(required=1),
                'object.objectType': dict(required=1),
                'context':           dict(required=0),
              }

    def buildObject(self):
        """
        Updates the dict content with the activity structure,
        with data from the request
        """
        ob = {'actor': {
                    'objectType': 'person',
                    '_id': self.data['actor']['_id'],
                    'displayName': self.data['actor']['displayName']
                    },
                'verb': 'post',
                'object': {
                    'objectType': 'note',
                    'content': self.data['object']['content']
                    }
                }
        if 'target' in self.data:
            ob['target'] = self.data['target']

        self.update(ob)


class User(MADBase):
    """
    """
    collection = 'users'
    unique = 'displayName'
    schema = {
                '_id':          dict(required=0),
                'displayName':  dict(required=1),
                'last_login':   dict(required=0),
                'following':    dict(required=0),
                'subscribedTo': dict(required=0),
                'published':    dict(required=0),
             }

    params = {
                'displayName':  dict(required=1),
             }

    def buildObject(self):
        """
        Updates the dict content with the activity structure,
        with data from the request
        """
        ob = {'displayName': self.data['displayName'],
                   'last_login': datetime.datetime.now(),
                   'following': {'items': [], },
                   'subscribedTo': {'items': [], }
                   }
        self.update(ob)
