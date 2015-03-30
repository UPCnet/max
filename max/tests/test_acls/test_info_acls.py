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

import os
import unittest


class InfoACLTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(os.path.dirname(__file__))

        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('messages')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)

    def test_get_public_settings(self):
        """
            Given i'm an unauthenticated user
            When i try to get max public settings
            Then i succeed
        """
        self.testapp.get('/info', status=200)

    def test_get_full_settings(self):
        """
            Given i'm an unauthenticated user
            When i try to get all max settings
            Then i get a Forbidden Error
        """
        self.testapp.get('/info/settings', status=401)

    def test_get_full_settings_authenticated(self):
        """
            Given i'm a regular user
            When i try to get all max settings
            Then i get a Forbidden Error
        """
        username = 'sheldon'
        self.create_user(username)
        self.testapp.get('/info/settings', headers=oauth2Header(username), status=403)

    def test_get_full_settings_as_manager(self):
        """
            Given i'm a Manager
            When i try to get all max settings
            Then i succeed
        """
        self.testapp.get('/info/settings', headers=oauth2Header(test_manager), status=200)

    def test_get_endpoints_info(self):
        """
            Given i'm an unauthenticated user
            When i try to get the endpoint definitions
            Then i succeed
        """
        self.testapp.get('/info/api', status=200)
