import os
import unittest
import doctest

from paste.deploy import loadapp

from max.tests.base import MaxTestBase, oauth2Header
from max.tests import test_default_security

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_ONLY_FIRST_FAILURE)


class DoctestCase(unittest.TestCase):
    def __new__(self, test):
        return getattr(self, test)()

    @classmethod
    def test_docs(cls):
        import manuel.testing
        import manuel.codeblock
        import manuel.doctest
        import manuel.capture
        m = manuel.doctest.Manuel(optionflags=OPTIONFLAGS)
        m += manuel.codeblock.Manuel()
        m += manuel.capture.Manuel()

        import pkg_resources

        return manuel.testing.TestSuite(
            m,
            os.path.join(pkg_resources.get_distribution('max').location,
                         'docs', 'ca', 'apirest.rst'),
            os.path.join(pkg_resources.get_distribution('max').location,
                         'docs', 'ca', 'apioperations.rst'),
            setUp=cls.setUp,
            tearDown=cls.tearDown,
        )

    @staticmethod
    def setUp(test):
        conf_dir = os.path.dirname(__file__)
        app = loadapp('config:tests.ini', relative_to=conf_dir)
        app.registry.max_store.drop_collection('users')
        app.registry.max_store.drop_collection('activity')
        app.registry.max_store.drop_collection('contexts')
        app.registry.max_store.drop_collection('conversations')
        app.registry.max_store.drop_collection('messages')
        app.registry.max_store.drop_collection('security')
        app.registry.max_store.security.insert(test_default_security)
        from webtest import TestApp
        testapp = TestApp(app)

        test.globs['testapp'] = testapp
        test.globs['oauth2Header'] = oauth2Header
        test.globs['MaxTestBase'] = MaxTestBase

    @staticmethod
    def tearDown(test):
        test.globs.clear()
        import pyramid.testing
        pyramid.testing.tearDown()
