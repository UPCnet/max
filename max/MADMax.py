# -*- coding: utf-8 -*-
#MADMax  Mongo Access Delegate for Max

from max.exceptions import ObjectNotFound

from bson.objectid import ObjectId
from pymongo import ASCENDING
from pymongo import DESCENDING

from max.utils.dicts import deepcopy
import sys

UNDEF = "__NO_DEFINED_VALUE_FOR_GETATTR__"


def ItemWrapper(item, request, collection, flatten=0, **kwargs):
    """
        Transforms a mongoDB item to a wrapped representation of it using
        the appropiate class, mapped by the origin collection of the item.
        Flattened or not by demand
    """
    CLASS_COLLECTION_MAPPING = getattr(sys.modules['max.models'], 'CLASS_COLLECTION_MAPPING', {})
    model = getattr(sys.modules['max.models'], CLASS_COLLECTION_MAPPING[collection], None)
    wrapped = model.from_object(request, item)

    # Also wrap subobjects, only if we are not flattening
    if not flatten and 'object' in wrapped:
        WrapperClass = wrapped.getObjectWrapper(wrapped['object']['objectType'])
        wrapped['object'] = WrapperClass(request, wrapped['object'], creating=False)

    if flatten:
        return wrapped.flatten(**kwargs)
    else:
        return wrapped


class ResultsWrapper(object):
    """
        Wraps a list of results to provide a flag
        showing if there are more items left to show.
    """
    def __init__(self, request, cursor, limit, flatten, keep_private_fields):
        """
            Slice the results, and set remaining flag if there are more items
            in the results that the limit specified.

            Queries with limit are executed with limit + 1, so, if we have
            more result items thatn the limit says, it mens that the query that
            originated this results has items remaining.

            Returns a generator that yields wrapped results until limit. If limit overpassed at
            least by one item, remaining flat will be set True

        """
        self.remaining = False
        self.collection = cursor.collection.name
        self.yielded = 0
        self.limit = limit
        self.request = request
        self.cursor = cursor
        self.flatten = flatten
        self.keep_private_fields = keep_private_fields
        self.generator = self.results()

    def results(self):
        for result in self.cursor:
            self.yielded += 1
            if self.limit > 0 and self.yielded > self.limit:
                self.remaining = True
                break
            yield ItemWrapper(
                result,
                self.request,
                self.collection,
                flatten=self.flatten,
                keep_private_fields=self.keep_private_fields)

    def __iter__(self):
        return self.generator.__iter__()

    def next(self):
        return self.generator.next()

    def get(self, count=None):
        result = []
        while True:
            try:
                result.append(self.generator.next())
            except:
                break
            if len(result) == count:
                break

        return result


class MADMaxCollection(object):
    """
        Wrapper for accessing collections
    """

    def __init__(self, request, collection, query_key='_id', field_filter=None):
        """
            Wrapper for accessig a collection. Acces to items can be performed dict-like using "_id" as
            key for finding items, or any field specified in "query_key". Anything passed in query_key must have unique values
            as we will perform find_one queries for dict-like access
        """
        self.request = request
        self.query_key = query_key
        self.show_fields = field_filter

        self.collection = getattr(request.db.db, collection, None)

    def setVisibleResultFields(self, fields):
        """
            Sets which fields to be returned in the query
        """
        if fields:
            self.show_fields = dict([(fieldname, 1) for fieldname in fields])
        else:
            self.show_fields = None

    def search(self, query, keep_private_fields=True, count=False, **kwargs):
        """
            Performs a search on the mongoDB
            Kwargs may contain:
                limit: Count of objects to be returned from search
                before: An id pointing to an activity, whose older fellows will be fetched
                after: An id pointing to an activity, whose newer fellows will be fetched
                hashtag: A list of hastags to filter activities by
                keywords: A list of keywords to filter activities by
                actor: A username to filter activities by actor
                tags: A list of tags to filter contexts
                object_tags: A list of tags to filter context activities
                twitter_enabled: Boolean for returning objects Twitter attributes
        """
        search_query = deepcopy(query)

        # Extract known params from kwargs
        limit = kwargs.get('limit', None)
        flatten = kwargs.get('flatten', 0)
        after = kwargs.get('after', None)
        before = kwargs.get('before', None)
        hashtag = kwargs.get('hashtag', None)
        keywords = kwargs.get('keywords', None)
        actor = kwargs.get('actor', None)
        favorites = kwargs.get('favorites', None)
        username = kwargs.get('username', None)
        tags = kwargs.get('tags', None)
        context_tags = kwargs.get('context_tags', None)
        twitter_enabled = kwargs.get('twitter_enabled', None)
        sort_direction = kwargs.get('sort_direction', DESCENDING)
        sort_params = kwargs.get('sort_params', [('_id', sort_direction)])
        date_filter = kwargs.get('date_filter', None)
        show_fields = kwargs.get('show_fields', None)
        offset_field = kwargs.get('offset_field', None)
        max_users = kwargs.get('max_users', None)

        sort_by_field = kwargs.get('sort_by_field', None)
        if sort_by_field:
            sort_params = [(sort_by_field, sort_direction)]

        # After & before contains the ObjectId of the offset that
        # we must use to skip results when paging results.
        # Depending on which of the two params is used, we'll determine
        # the direction of the filtering and store the actual offset
        # in its definitive variable query offset.
        if after or before:
            condition = after and '$gt' or '$lt'
            offset = after and after or before
        else:
            # conflicting offset definition will get no offset
            offset = None

        if max_users:
            sort_direction=ASCENDING
            sort_params = [(sort_by_field, sort_direction)]

        # If we have an offset defined, insert the filtering condition
        # on the search query.
        if offset:
            if max_users:
                default_offset_field = 'displayName'
            else:
                default_offset_field = sort_params[0][0] if sort_params else '_id'
            offset_field = offset_field if offset_field else default_offset_field
            search_query.update({offset_field: {condition: offset}})

        if hashtag:
            # Filter the query to only objects containing certain hashtags
            # Filter the query to only objects containing certain hashtags
            hashtag_query = {'object._hashtags': {'$all': hashtag}}
            search_query.update(hashtag_query)

        if actor:
            # Filter the query to only objects containing certain hashtags
            username_query = {'actor.username': actor}
            search_query.update(username_query)

        if favorites:
            # filter the query to only objectes favorited by the requesting actor
            favorites_query = {'favorites.username': favorites}
            search_query.update(favorites_query)

        if keywords:
            keyword_field = '_keywords'
            # XXX Temporary fix to filter by comment keywords
            if search_query.get('verb') == 'comment':
                keyword_field = 'object._keywords'
            # Filter the query to only objects containing certain keywords
            keywords_query = {keyword_field: {'$all': keywords}}
            search_query.update(keywords_query)

        if username:
            # Filter the query to only objects containing certain hashtags
            username_query = {
                "$or": [
                    {"username": {"$regex": username, "$options": "i", }},
                    {"displayName": {"$regex": username, "$options": "i", }}
                ]
            }
            search_query.update(username_query)

        if tags:
            # Filter the query to only objects containing certain tags
            tags_query = {'tags': {'$all': tags}}
            search_query.update(tags_query)

        if context_tags:
            # Filter the query to only objects containing certain tags
            object_tags_query = {'contexts.tags': {'$all': context_tags}}
            search_query.update(object_tags_query)

        if twitter_enabled:
            # Filter the query to only objects (contexts) containing a certain
            # twitter_hashtag
            twe_query = {
                "$or": [
                    {"twitterUsername": {"$exists": True}},
                    {"twitterHashtag": {"$exists": True}},
                ]
            }
            search_query.update(twe_query)

        if date_filter:
            # Filter the query to objects matching a specific published date range
            search_query.update({'published': date_filter})

        # Catch mixed unoptimal $or queries and reformulate
        if '$or' in search_query and len(search_query.keys()) > 1:
            mixed_specs = {key: value for key, value in search_query.items() if key != '$or' and key != 'actor.username'}
            for spec in search_query['$or']:
                spec.update(mixed_specs)
            for spec in mixed_specs:
                del search_query[spec]

        # Cursor is lazy, but better to execute search here for mental sanity
        self.setVisibleResultFields(show_fields)

        if max_users:
            cursor = self.collection.find(search_query, self.show_fields, sort=[('displayName',1)], limit=limit)
        else:
            cursor = self.collection.find(search_query, self.show_fields)

            # Sort the results
            cursor = cursor.sort(sort_params)

            if limit:
                cursor = cursor.limit(limit + 1)


        # If it's a count search, return the cursor's count before sorting and limiting
        if count:
            return cursor.count()


        # Unpack the lazy cursor,
        # Wrap the result in its Mad Class,
        # and flattens it if specified

        return ResultsWrapper(self.request, cursor, flatten=flatten, keep_private_fields=keep_private_fields, limit=limit)

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

    def _getItemsByFieldName(self, fieldname, value):
        """
            Constructs and executes a query on a single fieldname:value pair

            XXX TODO : Check if fieldname exists in the current collection
        """
        query = {}
        query[fieldname] = value
        return self.search(query)

    def wrapped_find_one(self, query, wrap=True, **kwargs):
        item = self.collection.find_one(query, self.show_fields, **kwargs)
        if item:
            if wrap:
                wrapped = ItemWrapper(item, self.request, self.collection.name)
                wrapped.__parent__ = self
            else:
                return item
            return wrapped

    def __getitem__(self, itemID):
        """
            Returns an unique item of the collection
        """
        if itemID == '_owner':
            return None
        query = self._getQuery(itemID)
        item = self.wrapped_find_one(query)
        if item is None:
            querykey = len(query.keys()) == 1 and query.keys()[0] or 'id'
            raise ObjectNotFound("Object with %s %s not found inside %s" % (querykey, itemID, self.collection.name))

        return item

    def __getattr__(self, name):
        """
            Enables single field queries on the collection,  by calling dynamically-created functions
            with the form myCollection.getItemsByFieldName, where 'FieldName' is a known field of the collection's items.
        """
        if name.startswith('getItemsBy'):
            fieldname = name[10:]
            return lambda value: self._getItemsByFieldName(fieldname, value)
        else:
            raise AttributeError(name)

    def first(self, query={}, flatten=False):
        return self.wrapped_find_one(query, wrap=not flatten, sort=[('_id', ASCENDING)])

    def last(self, query={}, flatten=False):
        return self.wrapped_find_one(query, wrap=not flatten, sort=[('_id', DESCENDING)])

    def dump(self, flatten=0, **kwargs):
        """
            Returns all records of a collection
        """

        return self.search({}, flatten=flatten, **kwargs)

    def remove(self, query, logical=False):
        """
            deletes items matched by query, or marks as not visible if logical.
        """
        if logical:
            self.collection.update(query, {'$set': {'visible': False}}, multi=True)
        else:
            self.collection.remove(query)


class MADMaxDB(object):
    """ Wrapper for accessing Database and a specific collection via a class attribute.

        usage: MADMaxDB.<name_of_the_collection>
    """

    def __init__(self, request, db):
        """
        """
        self.request = request
        self.db = db

    def __getattr__(self, name):
        """
            Returns a MADMaxCollection wrapper or a class attribute. Raises AttributeError if nothing found
        """
        return MADMaxCollection(self.request, name)
