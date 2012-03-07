import unittest
import os
from paste.deploy import loadapp
from mock_http import MockHTTP, GET


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        from webtest import TestApp
        self.testapp = TestApp(self.app)

    # def test_root(self):
    #     res = self.testapp.get('/', status=200)
    #     self.failUnless('Pyramid' in res.body)


class MockOAuthServerTest(unittest.TestCase):
    """Demonstrates the use of the MockHttpServer from client code."""
    def setUp(self):
        self.mockoauth = MockHTTP(8080)
        self.mockoauth.expects(method=GET, path='/checktoken').will(body='')

    def test_simple_get(self):
        import requests
        result = requests.get('http://localhost:8080/checktoken')
        self.assertEqual(result.text, '')
