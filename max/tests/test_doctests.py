import os
import unittest
import doctest
import json

from httpretty import HTTPretty
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, oauth2Header, basicAuthHeader
from max.tests import test_manager, test_default_security

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_ONLY_FIRST_FAILURE)


class mock_post(object):

    def __init__(self, *args, **kwargs):
        pass

    text = ""
    status_code = 200


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
        app.registry.max_store.drop_collection('security')
        app.registry.max_store.security.insert(test_default_security)
        from webtest import TestApp
        testapp = TestApp(app)

        # create_user(testapp, 'messi')

        test.globs['testapp'] = testapp
        test.globs['oauth2Header'] = oauth2Header
        test.globs['popIdfromResponse'] = popIdfromResponse
        test.globs['MaxTestBase'] = MaxTestBase

    @staticmethod
    def tearDown(test):
        test.globs.clear()
        import pyramid.testing
        pyramid.testing.tearDown()


def create_user(testapp, username):
    HTTPretty.enable()
    HTTPretty.register_uri(HTTPretty.POST, "http://localhost:8080/checktoken",
                           body="",
                           status=200)
    testapp.post('/people/%s' % username, "", oauth2Header(test_manager), status=201)


def create_context(testapp, context, permissions=None, expect=201):
    default_permissions = dict(read='public', write='public', join='public', invite='subscribed')
    new_context = dict(context)
    if 'permissions' not in new_context:
        new_context['permissions'] = default_permissions
    if permissions:
        new_context['permissions'].update(permissions)
    res = testapp.post('/contexts', json.dumps(new_context), oauth2Header(test_manager), status=expect)
    return res


def popIdfromResponse(response):
    result = json.loads(response)
    del result['items'][0]['id']
    return result
