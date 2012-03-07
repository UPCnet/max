import unittest
import os
from paste.deploy import loadapp
from mock_http import MockHTTP, GET
import base64


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        from webtest import TestApp
        self.testapp = TestApp(self.app)

    def test_add_user(self):
        username = 'messi'
        res = self.testapp.post('/people/%s' % username, {}, basicAuthHeader('operations', 'operations'), status=201)
        # TODO: comprovar que es semblant a:
        # u'{"username": "messi", "subscribedTo": {"items": []}, "last_login": "2012-03-07T22:32:19Z", "published": "2012-03-07T22:32:19Z", "following": {"items": []}, "id": "4f57e1f3530a693147000000"}'


class MockOAuthServerTest(unittest.TestCase):
    """Demonstrates the use of the MockHttpServer from client code."""
    def setUp(self):
        self.mockoauth = MockHTTP(8080)
        self.mockoauth.expects(method=GET, path='/checktoken').will(body='')

    def test_simple_get(self):
        import requests
        result = requests.get('http://localhost:8080/checktoken')
        self.assertEqual(result.text, '')


def basicAuthHeader(username, password):
    base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
    return dict(Authorization="Basic %s" % base64string)
