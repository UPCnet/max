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
        self.app.registry.max_store.drop_collection('tokens')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)

    def tearDown(self):
        import pyramid.testing
        pyramid.testing.tearDown()

    # BEGIN TESTS

    def test_add_device_token_ios(self):
        username = 'messi'
        platform = 'ios'
        token = '12345678901234567890123456789012'
        self.create_user(username)
        res = self.testapp.post('/people/%s/device/%s/%s' % (username, platform, token), "", oauth2Header(username), status=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('token', ''), token)
        self.assertEqual(result.get('platform', ''), platform)

    def test_add_device_token_android(self):
        username = 'messi'
        platform = 'android'
        token = '12345678901234567890123456789012klhsdflajshdfkjashdfoq'
        self.create_user(username)
        res = self.testapp.post('/people/%s/device/%s/%s' % (username, platform, token), "", oauth2Header(username), status=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('token', ''), token)
        self.assertEqual(result.get('platform', ''), platform)

    def test_add_device_invalid_platform(self):
        username = 'messi'
        platform = 'blackberry'
        token = '12345678901234567890123456789012klhsdflajshdfkjashdfoq'
        self.create_user(username)
        self.testapp.post('/people/%s/device/%s/%s' % (username, platform, token), "", oauth2Header(username), status=400)

    def test_delete_device_token(self):
        username = 'messi'
        platform = 'ios'
        token = '12345678901234567890123456789012'
        self.create_user(username)
        self.testapp.post('/people/%s/device/%s/%s' % (username, platform, token), "", oauth2Header(username), status=201)
        self.testapp.delete('/people/%s/device/%s/%s' % (username, platform, token), "", oauth2Header(username), status=204)
