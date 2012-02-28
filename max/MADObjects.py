from max.rest.utils import extractPostData, flatten, RUDict
from max.exceptions import MissingField, ObjectNotSupported, DuplicatedItemError, UnknownUserError
import datetime
from pyramid.request import Request
import sys


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
            Checks if all the required schema fields (required=1) are present in
            the collected data
        """
        for fieldname in self.schema:
            if self.schema.get(fieldname).get('required', 0):
                if not self.checkParameterExists(fieldname):
                    raise MissingField, 'Required parameter "%s" not found in the request' % fieldname
        return True


class MADBase(MADDict):
    """
        Base Class for Objects in the MongoDB, It can be instantiated with a MongoDB Object
        or a request object in the source param.

        If instantiated with a MongoDB Object the collection where the object must be passed
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
            record on the DB and set it as actor. Also provides the user object with default
            displayName if not set.
        """
        if 'actor' in self.data:
            if '_id' not in self.data['actor'].keys():
                user_username = self.data['actor']['username']
                user = self.mdb_collection.database.users.find_one({'username': user_username})
                if user != None:
                    user.setdefault('displayName', user['username'])
                    self.data['actor'] = user
                else:
                    raise UnknownUserError, 'Unknown user "%s"' % user_username

    def insert(self):
        """
            Inserts the item into his defined collection and returns its _id
        """
        oid = self.mdb_collection.insert(self)
        return str(oid)

    def addToList(self, field, obj, allow_duplicates=False, safe=True):
        """
            Updates an array field of a existing DB object appending the new object
            and incrementing the totalItems counter.

            if allow_duplicates = True, allows to add items even if its already on the list. If not
            , looks for `safe` value to either raise an exception if safe==False or pass gracefully if its True

            XXX TODO allow object to be either a single object or a list of objects
        """

        obj_list = self.get(field, {'items': [], 'totalItems': 0})

        items = '%s.items' % field
        count = '%s.totalItems' % field

        duplicated = obj in obj_list['items']

        if allow_duplicates or not duplicated:
            self.mdb_collection.update({'_id': self['_id']},
                                      {'$push': {items: obj},
                                       '$inc': {count: 1}
                                      }
                                     )
        else:
            if not safe:
                raise DuplicatedItemError, 'Item already on list "%s"' % (field)

    def deleteFromList(self, field, obj, safe=True):
        """
            Updates an array field of a existing DB object removing the object

            If safe == False, don't perform any deletion, otherwise remove the found objects.
        """
        pass

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

    def getObjectWrapper(self, objType):
        """
            Get the apppopiate class to be inserted in the object field
            of (mainly) an Activity
        """
        module_name = objType.capitalize()
        module = getattr(sys.modules['max.ASObjects'], module_name, None)
        if module:
            return module
        else:
            raise ObjectNotSupported, 'Activitystrea.ms object type %s unknown or unsupported' % objType

    def updateFields(self, fields):
        return self.mdb_collection.update({'_id': self['_id']},
                                          {'$set': fields, },)
