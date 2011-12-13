import time
from rfc3339 import rfc3339
from max.rest.utils import extractPostData
from pymongo.objectid import ObjectId

class MADBase(dict):
    """A simple vitaminated dict for holding a MongoBD arbitrary object"""

    schema = []
    collection = ''
    mdb_collection = None  

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

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
        if hasattr(self,key):
            dict.__setattr__(self,key,value)
        else:
            self.__setitem__(key, value)
    
    def __getattr__(self, key):
        """
        Maps dict items access to attributes, while preserving access to class attributes
        """
        return getattr(self,key,self.__getitem__(key))

    def insert(self):
        """
        Inserts the item into his defined collection
        """
        self.mdb_collection.insert(self)


class Activity(MADBase):
    
    collection = 'activity'
    schema = {
                '_id':       dict(required=1),
                'actor':     dict(required=1),
                'verb':      dict(required=1),
                'object':    dict(required=1),
                'published': dict(required=1),
                'target':    dict(required=0),
             }

    def __init__(self, request, *args, **kwargs):
        self.mdb_collection = request.context.db[self.collection]
        self['published'] = rfc3339(time.time())
        self.buildObject(extractPostData(request))

    def buildObject(self,data):
        """
        Updates the dict contentwith the activity structure, 
        with data from the request
        """
        ob =  {'actor': {
                    'objectType': 'person',
                    '_id': ObjectId(data['actor']['id']),
                    'displayName': data['actor']['displayName']
                    },
                'verb': 'post',
                'object': {
                    'objectType': 'note',
                    'content': data['object']['content']
                    }
                }
        if 'target' in data:
            ob['target'] = data['target']

        self.update(ob)
        
    def addComment(self,object):
        """
        """
        pass


# import transaction

# from sqlalchemy.orm import scoped_session
# from sqlalchemy.orm import sessionmaker

# from sqlalchemy.ext.declarative import declarative_base

# from sqlalchemy.exc import IntegrityError

# from sqlalchemy import Integer
# from sqlalchemy import Unicode
# from sqlalchemy import Column

# from zope.sqlalchemy import ZopeTransactionExtension

# DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
# Base = declarative_base()

# class MyModel(Base):
#     __tablename__ = 'models'
#     id = Column(Integer, primary_key=True)
#     name = Column(Unicode(255), unique=True)
#     value = Column(Integer)

#     def __init__(self, name, value):
#         self.name = name
#         self.value = value

# class MyRoot(object):
#     __name__ = None
#     __parent__ = None

#     def __getitem__(self, key):
#         session= DBSession()
#         try:
#             id = int(key)
#         except (ValueError, TypeError):
#             raise KeyError(key)

#         item = session.query(MyModel).get(id)
#         if item is None:
#             raise KeyError(key)

#         item.__parent__ = self
#         item.__name__ = key
#         return item

#     def get(self, key, default=None):
#         try:
#             item = self.__getitem__(key)
#         except KeyError:
#             item = default
#         return item

#     def __iter__(self):
#         session= DBSession()
#         query = session.query(MyModel)
#         return iter(query)

# root = MyRoot()

# def root_factory(request):
#     return root

# def populate():
#     session = DBSession()
#     model = MyModel(name=u'test name', value=55)
#     session.add(model)
#     session.flush()
#     transaction.commit()

# def initialize_sql(engine):
#     DBSession.configure(bind=engine)
#     Base.metadata.bind = engine
#     Base.metadata.create_all(engine)
#     try:
#         populate()
#     except IntegrityError:
#         transaction.abort()
#     return DBSession

# def appmaker(engine):
#     initialize_sql(engine)
#     return root_factory
