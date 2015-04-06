# -*- coding: utf-8 -*-
from bson import json_util
from bson.objectid import ObjectId
from copy import copy
from datetime import datetime
from rfc3339 import rfc3339


class RUDict(dict):

    def __init__(self, *args, **kw):
        super(RUDict, self).__init__(*args, **kw)

    def update(self, new):
        """
        """
        from max.MADObjects import MADDict

        def recursive_update(old, new):
            for key, value in new.items():
                # If We found a key on new that is
                # present on old, and the key's value
                # is a dict we must recurse the child keys
                # Any other case replaces or adds the new value
                is_plain_dict = isinstance(value, dict) and not isinstance(value, MADDict)
                if key in old and is_plain_dict:

                    recursive_update(old[key], value)
                else:
                    old[key] = value if not is_plain_dict else copy(value)
            old = copy(old)

        if new:
            recursive_update(self, new)


def deepcopy(original):
    """
        Faster deepcopy doing only the copy stuff and custom checks.
    """
    from max.MADObjects import MADDict

    def recurse_list(obj):
        out = list()
        for item in obj:
            out.append(process(item))
        return out

    def recurse_dict(obj):
        out = dict().fromkeys(obj)
        for k, v in obj.iteritems():
            out[k] = process(v)
        return out

    def process(obj):
        if isinstance(obj, MADDict):
            return obj
        elif isinstance(obj, dict):
            return recurse_dict(obj)
        elif isinstance(obj, list):
            return recurse_list(obj)
        else:
            try:
                return obj.copy()   # dicts, sets
            except AttributeError:
                try:
                    return obj[:]   # lists, tuples, strings, unicode
                except:
                    return obj  # ints
        return obj  # other uncatched

    return process(original)


def decodeBSONEntity(di, key):
    """
        Inspired by pymongo bson.json_util.default, but specially processing some value types:

        ObjectId --> hexvalue
        datetime --> rfc3339

        Also, while json_util.default creates a new dict in the form {$name: decodedvalue} we assign
        the decoded value, 'flattening' the value directly in the field.

        Fallback to other values using json_util.default, and flattening only those decoded entities
        that has only one key.
    """
    value = di[key]
    if isinstance(value, ObjectId):
        di[key] = str(value)
        return
    if isinstance(value, datetime):
        di[key] = rfc3339(value, utc=True, use_system_timezone=False)
        return
    try:
        decoded = json_util.default(di[key])
        if len(decoded.keys()) == 1:
            di[key] = decoded[decoded.keys()[0]]
        else:
            di[key] = decoded
    except:
        pass


def deUnderescore(di, key):
    """
        Renames a dict key, removing underscores from the begginning of the key
    """
    if key.startswith('_'):
        newkey = key.lstrip('_')
        di[newkey] = di[key]
        di.pop(key, None)
        return newkey
    return key


def clearPrivateFields(di):
    """
        Clears all fields starting with _ except _id
    """
    for key in di.keys():
        if key.startswith('_') and key not in ['_id']:
            di.pop(key, None)


def flattendict(original, filter_method=None, **kwargs):
    """
        Flattens key/values of a dict and continues the recursion
    """
    di = original.copy()
    if not kwargs.get('keep_private_fields', True):
        clearPrivateFields(di)

    # Default is squashing anything or the specified fields in squash
    squash = kwargs.get('squash', [])
    preserve = kwargs.get('preserve', None)

    # If both parameters indicated, don't squash anything
    if 'preserve' in kwargs and 'squash' in kwargs:
        squash = []
    # If only preserved was indicated, squash
    elif preserve is not None:
        squash = set(di.keys()) - set(preserve)

    for key in di.keys():
        value = di[key]
        if isinstance(value, dict) or isinstance(value, list):
            di[key] = flatten(value, **kwargs)
        else:
            decodeBSONEntity(di, key)
        newkey = deUnderescore(di, key)
        if key in squash or newkey in squash:
            di.pop(newkey, None)

        if filter_method:
            do_filter = filter_method(key)
            if do_filter:
                di.pop(newkey, None)

    return di


def flatten(data, filter_method=None, **kwargs):
    """
        Recursively flatten a dict or list
    """
    if isinstance(data, list):
        newitems = []
        for item in data:
            newitems.append(flatten(item, **kwargs))
        data = newitems
    if isinstance(data, dict):
        data = flattendict(data, filter_method=filter_method, **kwargs)
    return data
