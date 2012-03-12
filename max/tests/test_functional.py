import unittest
import os
from paste.deploy import loadapp
from mock_http import MockHTTP, GET, POST
import base64
import json


class FunctionalTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.oauthserver = setupMockoAuthServer()

    @classmethod
    def tearDownClass(cls):
        cls.oauthserver.verify()

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        from webtest import TestApp
        self.testapp = TestApp(self.app)

    def create_user(self, username):
        self.testapp.post('/people/%s' % username, "", basicAuthHeader('operations', 'operations'), status=201)

    def test_add_user(self):
        username = 'messi'
        res = self.testapp.post('/people/%s' % username, "", basicAuthHeader('operations', 'operations'), status=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')
        # u'{"username": "messi", "subscribedTo": {"items": []}, "last_login": "2012-03-07T22:32:19Z", "published": "2012-03-07T22:32:19Z", "following": {"items": []}, "id": "4f57e1f3530a693147000000"}'

    def test_user_exist(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s' % username, "", basicAuthHeader('operations', 'operations'), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')

    def test_get_user(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')

    def test_get_user_not_me(self):
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.testapp.get('/people/%s' % username_not_me, "", oauth2Header(username), status=401)

    def test_get_non_existent_user(self):
        username = 'messi'
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'UnknownUserError')

    def test_modify_user(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.put('/people/%s' % username, json.dumps({"displayName": "Lionel Messi"}), oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('displayName', None), 'Lionel Messi')

    def test_modify_non_existent_user(self):
        username = 'messi'
        res = self.testapp.put('/people/%s' % username, json.dumps({"displayName": "Lionel Messi"}), oauth2Header(username), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'UnknownUserError')

    def test_get_all_users(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/people', "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 1)
        self.assertEqual(result.get('items', None)[0].get('username'), 'messi')


def basicAuthHeader(username, password):
    base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
    return dict(Authorization="Basic %s" % base64string)


def oauth2Header(username):
    return {"X-Oauth-Token": "jfa1sDF2SDF234", "X-Oauth-Username": username, "X-Oauth-Scope": "widgetcli"}


def setupMockoAuthServer():
    mockoauth = MockHTTP(8080)
    mockoauth.expects(method=POST, path='/checktoken').will(body='')
    return mockoauth


# class MockOAuthServerTest(unittest.TestCase):
#     """Demonstrates the use of the MockHttpServer from client code."""
#     @classmethod
#     def setUpClass(cls):
#         cls.oauthserver = MockHTTP(8080)
#         cls.oauthserver.expects(method=GET, path='/checktoken').will(body='')

#     @classmethod
#     def tearDownClass(cls):
#         cls.oauthserver.verify()

#     def test_simple_get(self):
#         import requests
#         result = requests.get('http://localhost:8080/checktoken')
#         self.assertEqual(result.text, '')
