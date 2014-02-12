# -*- coding: utf-8 -*-
import os
import json
import unittest
from functools import partial

from paste.deploy import loadapp
from mock import patch

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header, mock_post
from max.tests import test_manager, test_default_security


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests_vip.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

    def tearDown(self):
        import pyramid.testing
        pyramid.testing.tearDown()

    # BEGIN TESTS
    # !!! IMPORTANT INFO !!! All this tests are run with the max.restricted_user_visibility_mode=True in set the .ini

    def test_add_vip_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('VIP', username), "", oauth2Header(test_manager), status=201)

    def test_get_people_as_vip(self):
        """
            Given an admin user
            When I create a user
            Then the creator must be the admin user
        """
        usernamenotvip1 = 'user1'
        usernamenotvip2 = 'user2'
        usernamevip = 'user3'

        self.create_user(usernamenotvip1)
        self.create_user(usernamenotvip2)
        self.create_user(usernamevip)

        self.testapp.post('/admin/security/roles/%s/users/%s' % ('VIP', usernamevip), "", oauth2Header(test_manager), status=201)

        res = self.testapp.get('/people', json.dumps({"username": usernamenotvip1}), oauth2Header(usernamevip), status=200)

        self.assertEqual(len(res.json), 1)
        self.assertEqual(res.json['username'], usernamenotvip1)

