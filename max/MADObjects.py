# -*- coding: utf-8 -*-
from max.exceptions import DuplicatedItemError
from max.exceptions import MissingField
from max.exceptions import ObjectNotSupported
from max.exceptions import ValidationError
from max.rest.utils import RUDict
from max.rest.utils import flatten
from pyramid.security import ACLAllowed
from pyramid.threadlocal import get_current_request

from bson import ObjectId
from cgi import FieldStorage
from copy import deepcopy

import datetime
import sys


class MADDict(dict):
    """
        A simple vitaminated dict for holding a MongoBD arbitrary object
    """
    schema = {}

    def __getattr__(self, key):
        """
            Maps dict items access to attributes, while preserving access to class attributes.

            Wakes up objects from database when necessary.
        """
        try:
            # Try to get the requested attribute as a object contained item
            return self[key]
        except AttributeError as exc:
            raise exc

    def __setitem__(self, key, val):
        """
            Allow only fields defined in schema to be inserted in the dict
            ignore non schema values
        """
        if key in object.__getattribute__(self, 'schema'):
            dict.__setitem__(self, key, val)
        else:
            pass

    def __repr__(self):  # pragma: no cover
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).iteritems():
            if isinstance(self.get(k, None), dict) and isinstance(v, dict):
                self[k].update(v)
            else:
                self[k] = v

    def __setattr__(self, key, value):
        """
            Enables setting values of dict's items trough attribute assignment,
            while preserving default setting of class attributes
        """
        if key in object.__getattribute__(self, 'schema'):
            self.__setitem__(key, value)
        else:
            object.__setattr__(self, key, value)

    def _on_create_custom_validations(self):
        return True

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

    def checkFieldValueIsNotEmpty(self, data):
        """
        """
        if isinstance(data, str):
            return data != ''
        if isinstance(data, list):
            return data != []
        if isinstance(data, dict):
            return data != {}
        if isinstance(data, FieldStorage):
            return True
        else:
            if data:
                return True
            else:
                return False

    def processFields(self, updating=False):
        """
            Processes fields doing validations and formating

            - Checks for required fields present
            - Checks for emptyness of fields
            - Validates fields
            - Formats fields

            Returns a list of empty fields for future actions
        """
        for fieldname in self.schema:
            # Check required
            if self.schema.get(fieldname).get('required', 0):
                field_required = True

                # Raise an error unless we are updating
                if not self.checkParameterExists(fieldname) and not updating:
                    raise MissingField('Required parameter "%s" not found in the request' % fieldname)
            else:
                field_required = False

            # Check validators if fieldname is present in current data
            if fieldname in self.data:
                field_value = self.data.get(fieldname)
                if self.checkFieldValueIsNotEmpty(field_value):

                    # Validate and format
                    validators = self.schema.get(fieldname).get('validators', [])
                    for validator_name in validators:
                        validator = getattr(sys.modules['max.validators'], validator_name, None)
                        if validator:
                            success, message = validator(field_value)
                            if not success:
                                raise ValidationError('Validation error on field "%s": %s' % (fieldname, message))

                    # Apply formatters to validated fields
                    formatters = self.schema.get(fieldname).get('formatters', [])
                    for formatter_name in formatters:
                        formatter = getattr(sys.modules['max.formatters'], formatter_name, None)
                        if formatter:
                            try:
                                self.data[fieldname] = formatter(field_value)
                            except:
                                # XXX Fails silently if a formatter explodes
                                pass
                else:
                    # If field was required and we are not updating, raise
                    if field_required and not updating:
                        raise MissingField('Required parameter "%s" found but empty' % fieldname)
                    # Otherwise unset the field value by deleting it's key from the data and from the real object
                    del self.data[fieldname]
                    if fieldname in self:
                        del self[fieldname]


    # def validate(self):
    #     """
    #         Checks if all the required schema fields (required=1) are present in
    #         the collected data
    #         Executes custom validations if present
    #     """
    #     for fieldname in self.schema:
    #         # Check required
    #         if self.schema.get(fieldname).get('required', 0):
    #             if not self.checkParameterExists(fieldname):
    #                 raise MissingField, 'Required parameter "%s" not found in the request' % fieldname

    #         # Check validators if fieldname in current data
    #         if fieldname in self.data:
    #             validators = self.schema.get(fieldname).get('validators', [])
    #             for validator_name in validators:
    #                 validator = getattr(sys.modules['max.validators'], validator_name, None)
    #                 if validator:
    #                     success, message = validator(self.data.get(fieldname))
    #                     if success == False:
    #                         raise ValidationError, 'Validation error on field "%s": %s' % (fieldname, message)

    #     self._validate()
    #     return True


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
    default_field_view_permission = None
    default_field_edit_permission = None
    unique = ''
    collection = ''
    mdb_collection = None
    old = {}
    data = {}
    __parent__ = None

    def __init__(self):
        self.old = {}
        self.request = get_current_request()
        # When called from outside a pyramyd app, we have no request
        try:
            self.db = self.request.db
            self.mdb_collection = self.db[self.collection]
        except:
            pass
        self.data = RUDict({})

    def field_changed(self, field):
        return self.get(field, None) != self.old.get(field, None)

    def setDates(self):
        self['published'] = datetime.datetime.utcnow()

    def getOwner(self, request):
        return request.authenticated_userid

    def fromRequest(self, request, rest_params={}):
        self.data.update(self.request.decoded_payload)
        self.data.update(rest_params)

        # Since we are building from a request,
        # overwrite actor with the validated one from the request in source
        if 'actor' not in rest_params.keys():
            self.data['actor'] = request.actor

        # Who is actually doing this?
        # - The one that is authenticated
        self.data['_creator'] = request.authenticated_userid
        self.data['_owner'] = self.getOwner(request)

        self.processFields()

        # check if the object we pretend to create already exists
        existing_object = self.alreadyExists()
        if not existing_object:
            # if we are creating a new object, set the object dates.
            # It uses MADBase.setDates as default, override to set custom dates
            self.setDates()
            self._on_create_custom_validations()
            self.buildObject()
        else:
            # if it's already on the DB, just populate with the object data
            self.update(existing_object)

    def _post_init_from_object(self, source):
        return True

    def _before_saving_object(self):
        return True

    def _after_saving_object(self, oid):
        return True

    def _before_insert_object(self):
        return True

    def _after_insert_object(self, oid, **kwargs):
        return True

    def fromObject(self, source, collection=None):
        self.update(source)
        self.old.update(source)
        self.old = deepcopy(flatten(self.old))
        if 'id' in source:
            self['_id'] = source['id']
        self._post_init_from_object(source)

    def wake(self):
        """
            Tries to recover a lazy object from the database
        """
        obj = self.alreadyExists()
        if obj:
            self.update(obj)
            self.old.update(obj)
            self.old = deepcopy(flatten(self.old))

    def format_unique(self, key):
        return key if isinstance(key, ObjectId) else ObjectId(key)

    def fromDatabase(self, key):
        self.data[self.unique] = self.format_unique(key)
        self.wake()

    def reload(self):
        unique = self.unique
        value = self.get(unique)
        if value:
            query = {unique: value}
            reloaded = self.mdb_collection.find_one(query)
            self.update(reloaded)

    def reload__acl__(self):
        self.__acl__ = self.__class__.__acl__.wrapped(self)

    def insert(self, **kwargs):
        """
            Inserts the item into his defined collection and returns its _id
        """
        self._before_insert_object()
        oid = self.mdb_collection.insert(self)
        self._after_insert_object(oid, **kwargs)
        return str(oid)

    def save(self):
        """
            Updates itself to the database
        """
        self._before_saving_object()
        oid = self.mdb_collection.save(self)
        self._after_saving_object(oid)
        return str(oid)

    def _before_delete(self):
        """
            Executed before an object removal
            Override to provide custom behaviour on delete
        """
        pass

    def _after_delete(self):
        """
            Executed after an object removal
            Override to provide custom behaviour on delete
        """
        pass

    def delete(self):
        """
            Removes the object from the DB
        """
        self._before_delete()
        self.mdb_collection.remove({self.unique: self.format_unique(self[self.unique])})
        self._after_delete()

    def add_to_list(self, field, obj, allow_duplicates=False, safe=True):
        """ NEW METHOD NOT TAKING ACCOUNT OF 'items' and 'total Items'
            Updates an array field of a existing DB object appending the new object.

            if allow_duplicates = True, allows to add items even if its already on the list. If not
            , looks for `safe` value to either raise an exception if safe==False or pass gracefully if its True

            XXX TODO allow object to be either a single object or a list of objects
        """

        obj_list = self.get(field, [])
        if not isinstance(obj_list, list):
            raise AttributeError('Field {} is not a list.'.format(field))

        duplicated = obj in obj_list

        if allow_duplicates or not duplicated:
            # Self-update to reflect the addition
            self.setdefault(field, [])  # Make sure the field exists
            self[field].append(obj)

            # Validate field
            self.data = {field: obj}
            self.processFields(updating=True)

            # If valid, update
            self.mdb_collection.update({'_id': self['_id']},
                                       {'$push': {field: obj}}
                                       )
        else:
            if not safe:
                raise DuplicatedItemError('Item already on list "%s"' % (field))

    def delete_from_list(self, field, obj):
        """ NEW METHOD NOT TAKING ACCOUNT OF 'items' and 'total Items'
            Updates an array field of a existing DB object removing the object.

            If the array contains plain values, obj is the value to delete.
            If the array contains dicts, obj must be a dict to match its key-value with
            the value to delete on the array.

            XXX TODO allow object to be either a single object or a list of objects
        """

        self.mdb_collection.update({'_id': self['_id']}, {'$pull': {field: obj}})

    def alreadyExists(self):
        """
            Checks if there's an object with the value specified in the unique field.
            If present, return the object, otherwise returns None
        """
        unique = self.unique
        value = self.data.get(unique)
        if value:
            query = {unique: value}
            return self.mdb_collection.find_one(query)
        else:
            # in the case that we don't have the unique value in the request data
            # Assume that the object doesn't exist
            # XXX TODO - Test it!!
            return None

    def flatten(self, **kwargs):
        """
            Recursively transforms non-json-serializable values and simplifies
            $oid and $data BISON structures. Intended for final output
            Also removes fields starting with underscore _fieldname
        """
        dd = dict(self)
        return_dict = flatten(dd, **kwargs)
        visible_fields = self.get_visible_fields()
        for field, value in return_dict.items():
            if field not in visible_fields and field != 'objectType':
                del return_dict[field]
        return return_dict

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
            raise ObjectNotSupported('Activitystrea.ms object type %s unknown or unsupported' % objType)

    def updateFields(self, fields):
        """
            Update fields on objects
            where fields is a {name_field: value})
        """
        self.data = fields
        self.processFields(updating=True)
        self.update(fields)

    #
    # Security Related methods and properties
    #

    def get_default_permission_for(self, mode):
        """
            Returns the default permission for a field access type (view, edit)
        """
        return getattr(self, 'default_field_{}_permission'.format(mode), None)

    def get_field_permission_for(self, field, mode):
        """
            Returns the permission needed to have access to the field in the specified mode.
        """
        return self.schema[field].get(mode, self.get_default_permission_for(mode))

    def has_field_permission(self, field, mode):
        """
            Returns the name of the permission needed to grant permission_field.
            param permission_field MUST be "view" or "edit.
        """
        permission_name = self.get_field_permission_for(field, mode)
        return isinstance(self.request.has_permission(permission_name, self), ACLAllowed)

    def get_visible_fields(self):
        """
            Returns the real fieldname (without leading _) that
            the current authenticated user has permission to see
        """
        fields = []
        for field in self.schema:
            if self.has_field_permission(field, 'view'):
                fields.append(field.lstrip('_'))
        return fields

    # def get_visible_fields(self):
    #     """
    #         DEBUG VERSION, uncomment to debug field access
    #         Returns the real fieldname (without leading _) that
    #         the current authenticated user has permission to see
    #     """
    #     print
    #     print "********* FIELD ACCESS DEBUG for {} {}************".format(
    #         self.__class__.__name__,
    #         self.get(self.unique, 'unknown')
    #     )
    #     print "Request: {} {}".format(self.request.method, self.request.path)
    #     fields = []
    #     for field in self.schema:
    #         if self.has_field_permission(field, 'view'):
    #             fields.append(field.lstrip('_'))
    #         else:
    #             print '  User {} has no permission "{}{}" for field "{}" @ {}'.format(
    #                 self.request.authenticated_userid,
    #                 self.get_field_permission_for(field, 'view'),
    #                 ' [default]' if self.schema[field].get('view', None) is None else '',
    #                 field,
    #                 self.request.context.__class__.__name__
    #             )
    #     print "*****************************************"
    #     print
    #     return fields

    def get_editable_fields(self):
        """
            Returns the real fieldname (without leading _) on which
            the current authenticated userhas permission to edit
        """
        for fieldName in self.schema:
            if self.has_field_permission(fieldName, 'edit'):
                yield fieldName.lstrip('_')

    def getMutablePropertiesFromRequest(self, request):
        """
            Get the mutable properties base on the user's current roles
        """
        params = self.request.decoded_payload

        properties = {fieldName: params.get(fieldName) for fieldName in self.get_editable_fields() if params.get(fieldName, None) is not None}
        return properties
