import unittest

from pyramid import testing
from pyramid.testing import DummyRequest

import pymongo
import json
from bson import json_util

from max.mockers import demostatus_with_context, demostatus, demouser1, demouser2


class DummyRequestREST(DummyRequest):
    """ Enriquim la classe DummyRequest per a que tingui la propietat content_type """
    def __init__(self, params=None, environ=None, headers=None, path='/',
                 cookies=None, post=None, **kw):
        super(DummyRequestREST, self).__init__(params=params, environ=environ, headers=headers, path=path,
                 cookies=cookies, post=post, **kw)

        self.content_type = ""

testSettings = {'mongodb.url': 'mongodb://localhost', 'mongodb.db_name': 'testDB'}


class TestmaxREST(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=testSettings)

        # Create pre-populated test content
        request = DummyRequestREST()
        root = self._makeOne(request)
        self.user1 = root.db.users.insert(demouser1)
        self.user2 = root.db.users.insert(demouser2)

        # Substitute the test 'real' id of the test user
        # to fake the request as would be sent
        demostatus['actor']['_id'] = self.user1
        demostatus_with_context['actor']['_id'] = self.user1

        self.activity = root.db.activity.insert(demostatus)
        self.activityContext = root.db.activity.insert(demostatus_with_context)

    def tearDown(self):
        # Esborrar les dades de la BBDD de Test al finalitzar
        db_uri = testSettings['mongodb.url']
        conn = pymongo.Connection(db_uri)
        #conn.drop_database(testSettings['mongodb.db_name'])

        testing.tearDown()

    def _makeOne(self, request):
        from max.resources import Root
        return Root(request)

    def test_addUser(self):
        from max.rest.admin import addUser
        request = DummyRequestREST()
        root = self._makeOne(request)
        data = {'displayName': 'ferran'}
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = addUser(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_getUserActivity(self):
        from max.rest.query import getUserActivity
        request = DummyRequestREST()
        root = self._makeOne(request)
        data = {'displayName': 'victor'}
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = getUserActivity(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_getUserActivityQuery(self):
        from max.rest.query import getUserActivity
        request = DummyRequestREST(params={'displayName': 'victor'})
        root = self._makeOne(request)
        request.content_type = 'application/json'
        result = getUserActivity(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_getUserActivityWithScope(self):
        from max.rest.query import getUserActivity
        request = DummyRequestREST()
        root = self._makeOne(request)

        # Subscribe the user to a ficticious context
        root.db.users.update({'_id': self.user2},
                            {'$push': {'subscribedTo.items': {'url': 'http://atenea.upc.edu/introcomp'}},
                            '$inc': {'subscribedTo.totalItems': 1}})

        data = {'displayName': 'javier'}
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = getUserActivity(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_getUserActivityByScope(self):
        from max.rest.query import getUserActivityByScope
        request = DummyRequestREST()
        root = self._makeOne(request)

        data = {'displayName': 'victor', 'scopes': ['http://atenea.upc.edu/introcomp', 'http://atenea.upc.edu/456456']}
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = getUserActivityByScope(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_addActivity(self):
        from max.rest.activity import addActivity
        from max.mockers import user_status
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
        from max.rest.activity import addComment
        from max.mockers import user_comment
        request = DummyRequestREST()
        root = self._makeOne(request)

        data_comment = user_comment

        # Put the 'real' id with the user mock object as would be sent
        data_comment['actor']['id'] = str(self.user2)

        # Put the 'real' id with the activity mock object as would be sent
        inreplyto = {'id': str(self.activity)}

        del data_comment['object']['inReplyTo']
        data_comment['object']['inReplyTo'] = []
        data_comment['object']['inReplyTo'].append(inreplyto)

        # Do the request to the WS
        data_json = json.dumps(data_comment)
        request.content_type = 'application/json'
        request.body = data_json
        result = addComment(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_Follow(self):
        from max.rest.subscriptions import Follow
        from max.mockers import follow
        request = DummyRequestREST()
        root = self._makeOne(request)

        data = follow

        # Put the 'real' id with the user mock object as would be sent
        data['actor']['id'] = str(self.user1)
        data['object']['id'] = str(self.user2)

        # Do the request to the WS
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = Follow(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_unFollow(self):
        from max.rest.subscriptions import unFollow
        from max.mockers import unfollow
        request = DummyRequestREST()
        root = self._makeOne(request)

        data = unfollow

        # Put the 'real' id with the user mock object as would be sent
        data['actor']['id'] = str(self.user1)
        data['object']['id'] = str(self.user2)

        # Do the request to the WS
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = unFollow(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_followContext(self):
        from max.rest.subscriptions import followContext
        from max.mockers import follow_context
        request = DummyRequestREST()
        root = self._makeOne(request)

        data = follow_context

        # Put the 'real' id with the user mock object as would be sent
        data['actor']['id'] = str(self.user1)

        # Do the request to the WS
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = followContext(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_unfollowContext(self):
        from max.rest.subscriptions import unFollowContext
        from max.mockers import unfollow_context
        request = DummyRequestREST()
        root = self._makeOne(request)

        data = unfollow_context

        # Put the 'real' id with the user mock object as would be sent
        data['actor']['id'] = str(self.user1)

        # Do the request to the WS
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = unFollowContext(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_Like(self):
        from max.rest.ratings import Like
        from max.mockers import like
        request = DummyRequestREST()
        root = self._makeOne(request)

        data = like

        # Put the 'real' id with the user mock object as would be sent
        data['actor']['id'] = str(self.user2)
        data['object']['id'] = str(self.activity)

        # Do the request to the WS
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = Like(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))

    def test_Share(self):
        from max.rest.share import Share
        from max.mockers import share
        request = DummyRequestREST()
        root = self._makeOne(request)

        data = share

        # Put the 'real' id with the user mock object as would be sent
        data['actor']['id'] = str(self.user2)
        data['object']['id'] = str(self.activity)

        # Do the request to the WS
        data_json = json.dumps(data)
        request.content_type = 'application/json'
        request.body = data_json
        result = Share(root, request)
        self.assertEqual(result.status, '200 OK')
        self.assertTrue(isinstance(result.body, str))
