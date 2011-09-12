import unittest

from pyramid import testing
from pyramid.testing import DummyRequest

import pymongo
import json
from bson import json_util

from macs.activityDemos import demostatus, demouser1, demouser2

from copy import deepcopy

class DummyRequestREST(DummyRequest):
    """ Enriquim la classe DummyRequest per a que tingui la propietat content_type """
    def __init__(self, params=None, environ=None, headers=None, path='/',
                 cookies=None, post=None, **kw):
        super(DummyRequestREST, self).__init__(params=params, environ=environ, headers=headers, path=path,
                 cookies=cookies, post=post, **kw)

        self.content_type = ""

testSettings = {'mongodb.url': 'mongodb://localhost', 'mongodb.db_name': 'testDB'}


class TestMacsREST(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=testSettings)

        # Create pre-populated test content
        request = DummyRequestREST()
        root = self._makeOne(request)
        self.user1 = root.db.users.insert(demouser1)
        self.user2 = root.db.users.insert(demouser2)

        self.activity = root.db.activity.insert(demostatus)

    def tearDown(self):
        # Esborrar les dades de la BBDD de Test al finalitzar
        db_uri = testSettings['mongodb.url']
        conn = pymongo.Connection(db_uri)
        conn.drop_database(testSettings['mongodb.db_name'])

        testing.tearDown()

    def _makeOne(self, request):
        from macs.resources import Root
        return Root(request)

    def test_getUserActivity(self):
        from macs.rest.activity import getUserActivity
        request = DummyRequestREST()
        root = self._makeOne(request)
        data = {'actor.id': 'victor'}
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = getUserActivity(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_getUserActivityQuery(self):
        from macs.rest.activity import getUserActivity
        request = DummyRequestREST(params={'actor.id': 'victor'})
        root = self._makeOne(request)
        request.content_type = 'application/json'
        result = getUserActivity(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_addActivity(self):
        from macs.rest.activity import addActivity
        from macs.activityDemos import user_status
        request = DummyRequestREST()
        root = self._makeOne(request)
        data = user_status

        # Put the 'real' id with the user mock object as would be sent
        data['actor']['id'] = str(self.user1)

        # Do the request to the WS
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = addActivity(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_addComment(self):
        from macs.rest.activity import addComment
        from macs.activityDemos import user_comment
        request = DummyRequestREST()
        root = self._makeOne(request)

        data_comment = user_comment

        inreplyto = {'_id': self.activity}

        # Put the 'real' id with the user mock object as would be sent
        del data_comment['object']['inReplyTo']
        data_comment['object']['inReplyTo'] = []
        data_comment['object']['inReplyTo'].append(inreplyto)

        # Do the request to the WS
        data_json = json.dumps(data_comment, default=json_util.default)
        request.content_type = 'application/json'
        request.body = data_json
        result = addComment(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))


# def _initTestingDB():
#     from sqlalchemy import create_engine
#     from macs.models import initialize_sql
#     session = initialize_sql(create_engine('sqlite://'))
#     return session

# class TestMyRoot(unittest.TestCase):
#     def setUp(self):
#         self.config = testing.setUp()
#         #self.session = _initTestingDB()

#     def tearDown(self):
#         testing.tearDown()
#         #self.session.remove()

#     def _makeOne(self):
#         from macs.models import MyRoot
#         return MyRoot()

#     def test___getitem__hit(self):
#         from macs.models import MyModel
#         root = self._makeOne()
#         first = root['1']
#         self.assertEqual(first.__class__, MyModel)
#         self.assertEqual(first.__parent__, root)
#         self.assertEqual(first.__name__, '1')

#     def test___getitem__miss(self):
#         root = self._makeOne()
#         self.assertRaises(KeyError, root.__getitem__, '100')

#     def test___getitem__notint(self):
#         root = self._makeOne()
#         self.assertRaises(KeyError, root.__getitem__, 'notint')

#     def test_get_hit(self):
#         from macs.models import MyModel
#         root = self._makeOne()
#         first = root.get('1')
#         self.assertEqual(first.__class__, MyModel)
#         self.assertEqual(first.__parent__, root)
#         self.assertEqual(first.__name__, '1')

#     def test_get_miss(self):
#         root = self._makeOne()
#         self.assertEqual(root.get('100', 'default'), 'default')
#         self.assertEqual(root.get('100'), None)

#     def test___iter__(self):
#         root = self._makeOne()
#         iterable = iter(root)
#         result = list(iterable)
#         self.assertEqual(len(result), 1)
#         model = result[0]
#         self.assertEqual(model.id, 1)
