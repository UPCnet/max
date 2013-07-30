# -*- coding: utf-8 -*-
import os
import json
import requests
import unittest
from functools import partial
from webtest import http
from paste.deploy import loadapp
from mock import patch

from max.tests.base import MaxTestBase, oauth2Header, mock_post
from max.tests import test_manager, test_default_security


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:special_tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.server = http.StopableWSGIServer.create(self.app, port=8080)

    def create_user(self, username, expect=201, **kwargs):
        payload = {}
        for key, value in kwargs.items():
            payload[key] = value
        res = requests.request('post', '{}people/{}'.format(self.server.application_url, username), data=json.dumps(payload), headers=oauth2Header(test_manager))
        return res

    def test_upload_and_get_profile_avatar(self):
        username = 'messi'
        avatar_file = open(os.path.join(os.path.dirname(__file__), "avatar.png"), "rb")
        files = {'file': ('avatar.png', avatar_file)}
        self.create_user(username)
        res = requests.request('post', '{}people/{}/avatar'.format(self.server.application_url, username), headers=oauth2Header(username), files=files)
        self.assertEqual(res.status_code, 201)

        res = requests.request('get', '{}people/{}/avatar'.format(self.server.application_url, username))
        self.assertEqual(res.status_code, 200)

    def tearDown(self):
        self.server.shutdown()
        import pyramid.testing
        pyramid.testing.tearDown()
