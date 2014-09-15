# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header

from functools import partial
from mock import patch
from paste.deploy import loadapp

import json
import os
import unittest


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

    # BEGIN TESTS

    def test_root(self):
        """
            Test site root is accessible and returns html
        """
        res = self.testapp.get('/', status=200)
        self.assertEqual(res.content_type, 'text/html')

    def test_bad_test_call_warning(self):
        """
            Test calling a service with missing body parameter, and the authorization as body.
            As this will only probably happen in tests, The error message is targeted so.
        """
        username = 'messi'
        res = self.testapp.post('/people/%s' % username, oauth2Header(test_manager), status=401)
        self.assertEqual(res.json['error_description'], u'Authorization found in url params, not in request. Check your tests, you may be passing the authentication headers as the request body...')

    def test_bad_body_content_parsing(self):
        """
            Test calling a service with a list on post body, that expects nothing on it
            It should not fail, simply ignore content. Failures would be due a parsing error
            trying to extract actor information from the body.
        """
        username = 'messi'
        self.testapp.post('/people/%s' % username, '[]', oauth2Header(test_manager), status=201)

    def test_post_tunneling_on_delete(self):
        """
            Test that calling a endpoint with DELETE indirectly within a POST
            actually calls the real delete method
        """
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        headers = oauth2Header(test_manager)
        headers['X-HTTP-Method-Override'] = 'DELETE'
        self.testapp.post('/activities/{}'.format(activity_id), '', headers, status=204)

    def test_post_tunneling_on_put(self):
        """
            Test that calling a endpoint with PUT indirectly within a POST
            actually calls the real PUT method
        """

        username = 'messi'
        self.create_user(username)
        headers = oauth2Header(username)
        headers['X-HTTP-Method-Override'] = 'PUT'
        res = self.testapp.post('/people/{}'.format(username), json.dumps({"displayName": "Lionel Messi"}), headers, status=200)
        self.assertEqual(res.json['displayName'], 'Lionel Messi')
