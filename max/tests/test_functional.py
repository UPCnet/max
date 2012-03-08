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

    def create_user(self):
        username = 'messi'
        self.testapp.post('/people/%s' % username, "", basicAuthHeader('operations', 'operations'), status=201)

    def test_add_user(self):
        username = 'messi'
        res = self.testapp.post('/people/%s' % username, "", basicAuthHeader('operations', 'operations'), status=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')
        # u'{"username": "messi", "subscribedTo": {"items": []}, "last_login": "2012-03-07T22:32:19Z", "published": "2012-03-07T22:32:19Z", "following": {"items": []}, "id": "4f57e1f3530a693147000000"}'

    def test_user_exist(self):
        self.create_user()
        username = 'messi'
        res = self.testapp.post('/people/%s' % username, "", basicAuthHeader('operations', 'operations'), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')

    def test_get_user(self):
        self.create_user()
        username = 'messi'
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')


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
