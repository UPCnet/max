#MADMax  Mongo Access Delegate for Max

from pymongo.objectid import ObjectId

UNDEF = "__NO_DEFINED_VALUE_FOR_GETATTR__"

class MADMaxCollection(object):
    """
        Wrapper for accessing collections
    """

    def __init__(self,collection,query_key='_id',field_filter=None):
        """
            Wrapper for accessig a collection. Acces to items can be performed dict-like using "_id" as
            key for finding items, or any field specified in "query_key". Anything passed in query_key must have unique values
            as we will perform find_one queries for dict-like access
        """
        self.collection = collection
        self.query_key = query_key
        self.show_fields = field_filter

    def setVisibleResultFields(self, fields):
        """
        """
        self.show_fields = dict([(fieldname,1) for fieldname in fields])

    def _getQuery(self,itemID):
        """
            Constructs the query based on the field used as key
        """
        query = {}
        if self.query_key=='_id':
            query[self.query_key]=ObjectId(itemID)
        else:
            query[self.query_key]=itemID
        return query

    def _getItemsByFieldName(self,fieldname,value):
        """
            Constructs and executes a query on a single fieldname:value pair

            XXX TODO : Check if fieldname exists in the current collection 
        """
        query = {}
        query[fieldname]=value
        cursor = self.collection.find(query,self.show_fields)
        #unpack the lazy cursor
        return [result for result in cursor]
        
    def __getitem__(self,itemID):
        """
            Returns an unique item of the collection
        """
        query = self._getQuery(itemID)
        return self.collection.find_one(query,self.show_fields)

    def __getattr__(self,name):
        """
            Enables single field queries on the collection,  by calling dynamically-created functions
            with the form myCollection.getItemsByFieldName, where 'FieldName' is a known field of the collection's items.
        """
        if name.startswith('getItemsBy'):
            fieldname = name[10:]
            return lambda value: self._getItemsByFieldName(fieldname,value)
        else:
            getattr(self,name)

    def dump(self):
        """
            Returns all records of a collection
        """
        cursor = self.collection.find()
        return [result for result in cursor]

class MADMaxDB(object):
    """
        Wrapper for accessing Database
    """

    def __init__(self,db):
        """
        """
        self.db = db


    def __getattr__(self,name,default=UNDEF):
        """
            Returns a MADMaxCollection wrapper or a class attribute. Raises AttributeError if nothing found
        """
        #First we try to access a colleccion named "name"
        collection = getattr(self.db,name,None)
        if collection:
            return MADMaxCollection(collection)
        else:
            #If no collection found, try to get a class attribute
            try:
                attr = getattr(self,name)
            except:
                #If failed and user didn't pass a default value
                if default==UNDEF:
                    raise AttributeError, name
                else:
                    attr = default
            return attr
        
