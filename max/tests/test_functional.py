import unittest
import os
from paste.deploy import loadapp


class FunctionalTests(unittest.TestCase):
    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:test.ini', relative_to=conf_dir)
        from webtest import TestApp
        self.testapp = TestApp(self.app)

    def test_root(self):
        res = self.testapp.get('/', status=200)
        self.failUnless('Pyramid' in res.body)
