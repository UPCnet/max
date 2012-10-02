# -*- coding: utf-8 -*-
#MADMax  Mongo Access Delegate for Max

from max.exceptions import ObjectNotFound
from bson.objectid import ObjectId
import sys
from pymongo import DESCENDING

UNDEF = "__NO_DEFINED_VALUE_FOR_GETATTR__"


class MADMaxCollection(object):
    """
        Wrapper for accessing collections
    """

    def __init__(self, collection, query_key='_id', field_filter=None):
        """
            Wrapper for accessig a collection. Acces to items can be performed dict-like using "_id" as
            key for finding items, or any field specified in "query_key". Anything passed in query_key must have unique values
            as we will perform find_one queries for dict-like access
        """
        self.collection = collection
        self.query_key = query_key
        self.show_fields = field_filter

    def setQueryKey(self, key):
        """
            Sets the key from where dict-like access will be searched on. Must be
            a unique field of the object, because in this kind of access only a item is
            returned
        """
        self.query_key = key

    def setVisibleResultFields(self, fields):
        """
            Sets which fields to be returned in the query
        """
        if fields:
            self.show_fields = dict([(fieldname, 1) for fieldname in fields])
        else:
            self.show_fields = None

    def search(self, query, show_fields=None, flatten=0, sort=None, sort_dir=DESCENDING, **kwargs):
        """
            Performs a search on the mongoDB
            Kwargs may contain:
                limit: Count of objects to be returned from search
                before: An id pointing to an activity, whose older fellows will be fetched
                after: An id pointing to an activity, whose newer fellows will be fetched
                hashtag: A list of hastags to filter activities by
                keywords: A list of keywords to filter activities by
                author: A username to filter activities by author
        """

        #Extract known params from kwargs
        limit = kwargs.get('limit', None)
        after = kwargs.get('after', None)
        before = kwargs.get('before', None)
        hashtag = kwargs.get('hashtag', None)
        keywords = kwargs.get('keywords', None)
        author = kwargs.get('author', None)
        username = kwargs.get('username', None)

        if after or before:
            condition = after and '$gt' or '$lt'
            offset = after and after or before
        else:
            offset = None

        if offset:
            # Filter the query to return objects created later or earlier than the one
            # represented by offset (offset not included)
            query.update({'_id': {condition: offset}})

        if hashtag:
            # Filter the query to only objects containing certain hashtags
            hashtag_query = {'$and': []}
            for hasht in hashtag:
                hashtag_query['$and'].append({'object._hashtags': hasht})
            query.update(hashtag_query)

        if author:
            # Filter the query to only objects containing certain hashtags
            username_query = {'actor.username': author}
            query.update(username_query)

        if keywords:
            # Filter the query to only objects containing certain keywords
            keywords_query = {'$and': []}
            for keyw in keywords:
                keywords_query['$and'].append({'object._keywords': keyw})
            query.update(keywords_query)

        if username:
            # Filter the query to only objects containing certain hashtags
            username_query = {"username": {"$regex": username, "$options": "i", }}
            query.update(username_query)

        # Cursor is lazy, but better to execute search here for mental sanity
        self.setVisibleResultFields(show_fields)
        cursor = self.collection.find(query, self.show_fields)

        # Sort and limit the results if specified
        if sort:
            cursor = cursor.sort(sort, sort_dir)
        if limit:
            cursor = cursor.limit(limit)

        # Unpack the lazy cursor,
        # Wrap the result in its Mad Class,
        # and flattens it if specified
        return [self.ItemWrapper(result, flatten=flatten) for result in cursor]

    def _getQuery(self, itemID):
        """
            Constructs the query based on the field used as key
        """
        query = {}
        if self.query_key == '_id':
            query[self.query_key] = ObjectId(itemID)
        else:
            query[self.query_key] = itemID
        return query

    def ItemWrapper(self, item, flatten=0):
        """
            Transforms a mongoDB item to a wrapped representation of it using
            the appropiate class, mapped by the origin collection of the item.
            Flattened or not by demand
        """
        class_map = dict(activity='Activity',
                         users='User',
                         contexts='Context')

        model = getattr(sys.modules['max.models'], class_map[self.collection.name], None)
        wrapped = model()
        wrapped.fromObject(item, collection=self.collection)

        #Also wrap subobjects
        if 'object' in wrapped:
            wrapped['object'] = wrapped.getObjectWrapper(wrapped['object']['objectType'])(wrapped['object'], creating=False)

        if flatten:
            return wrapped.flatten()
        else:
            return wrapped

    def _getItemsByFieldName(self, fieldname, value):
        """
            Constructs and executes a query on a single fieldname:value pair

            XXX TODO : Check if fieldname exists in the current collection
        """
        query = {}
        query[fieldname] = value
        return self.search(query)

    def __getitem__(self, itemID):
        """
            Returns an unique item of the collection
        """
        query = self._getQuery(itemID)
        item = self.collection.find_one(query, self.show_fields)
        if item:
            return self.ItemWrapper(item)
        else:
            querykey = len(query.keys()) == 1 and query.keys()[0] or 'id'
            raise ObjectNotFound("Object with %s %s not found inside %s" % (querykey, itemID, self.collection.name))

    def __getattr__(self, name):
        """
            Enables single field queries on the collection,  by calling dynamically-created functions
            with the form myCollection.getItemsByFieldName, where 'FieldName' is a known field of the collection's items.
        """
        if name.startswith('getItemsBy'):
            fieldname = name[10:]
            return lambda value: self._getItemsByFieldName(fieldname, value)
        else:
            getattr(self, name)

    def dump(self, flatten=0):
        """
            Returns all records of a collection
        """

        return self.search({}, flatten=flatten)


class MADMaxDB(object):
    """ Wrapper for accessing Database and a specific collection via a class attribute.

        usage: MADMaxDB.<name_of_the_collection>
    """

    def __init__(self, db):
        """
        """
        self.db = db

    def __getattr__(self, name, default=UNDEF):
        """
            Returns a MADMaxCollection wrapper or a class attribute. Raises AttributeError if nothing found
        """
        #First we try to access a colleccion named "name"
        collection = getattr(self.db, name, None)
        if collection:
            return MADMaxCollection(collection)
        else:
            #If no collection found, try to get a class attribute
            try:
                attr = getattr(self, name)
            except:
                #If failed and user didn't pass a default value
                if default == UNDEF:
                    raise AttributeError(name)
                else:
                    attr = default
            return attr
