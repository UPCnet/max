# -*- coding: utf-8 -*-
"""
    Authentication tests

"""
import os
import json
import unittest
from functools import partial

from paste.deploy import loadapp
from mock import patch

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header, mock_post
from max.tests import test_default_security, test_manager


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

    def test_invalid_token(self):
        username = 'messi'
        res = self.testapp.post('/people/%s' % username, json.dumps({}), oauth2Header(test_manager, token='bad token'), status=401)
        self.assertEqual(res.json['error_description'], 'Invalid token.')

    def test_invalid_scope(self):
        username = 'messi'
        headers = oauth2Header(test_manager)
        headers['X-Oauth-Scope'] = 'Invalid scope'
        res = self.testapp.post('/people/%s' % username, "", headers, status=401)
        self.assertEqual(res.json['error_description'], 'The specified scope is not allowed for this resource.')
