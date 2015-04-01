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
        self.reset_database(self.app)
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)
    # BEGIN TESTS

    def test_invalid_token(self):
        username = 'messi'
        res = self.testapp.post('/people/%s' % username, json.dumps({}), oauth2Header(test_manager, token='bad token'), status=401)
        self.assertEqual(res.json['error_description'], 'Invalid token.')

    def test_invalid_token_TEMPORARY(self):
        from hashlib import sha1
        from .mockers import create_context

        mindundi = 'messi'
        self.create_user(mindundi)
        self.create_context(create_context, owner=mindundi)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1"}), oauth2Header(mindundi, token='bad token'), status=401)
        self.assertEqual(res.json['error_description'], 'Invalid token.')

    def test_invalid_scope(self):
        username = 'messi'
        headers = oauth2Header(test_manager)
        headers['X-Oauth-Scope'] = 'Invalid scope'
        res = self.testapp.post('/people/%s' % username, "", headers, status=401)
        self.assertEqual(res.json['error_description'], 'The specified scope is not allowed for this resource.')

    def test_invalid_scope_TEMPORARY(self):
        from hashlib import sha1
        from .mockers import create_context

        mindundi = 'messi'
        headers = oauth2Header(test_manager)
        headers['X-Oauth-Scope'] = 'Invalid scope'
        self.create_user(mindundi)
        self.create_context(create_context, owner=mindundi)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1"}), headers, status=401)
        self.assertEqual(res.json['error_description'], 'The specified scope is not allowed for this resource.')

    def test_required_user_not_found(self):
        from hashlib import sha1
        from .mockers import create_context

        mindundi = 'messi'
        self.create_context(create_context, owner=mindundi)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1"}), oauth2Header(mindundi), status=400)
        self.assertEqual(res.json['error_description'], 'Unknown actor identified by username: messi')

    def test_post_activity_no_auth_headers(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(user_status), status=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')
