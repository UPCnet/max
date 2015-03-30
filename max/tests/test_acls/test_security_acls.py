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


class SecurityACLTests(unittest.TestCase, MaxTestBase):

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

    def test_forbidden_access_to_security_settings(self):
        """
            Given i'm a regular user
            When i try to interact with security endpoints
            Then i get a Forbidden Exception
        """
        username = 'sheldon'

        self.testapp.get('/admin/security', headers=oauth2Header(username), status=403)
        self.testapp.get('/admin/security/users', headers=oauth2Header(username), status=403)
        self.testapp.get('/admin/security/roles/Manager/users/test_manager', headers=oauth2Header(username), status=403)
        self.testapp.post('/admin/security/roles/Manager/users/test_manager', headers=oauth2Header(username), status=403)
        self.testapp.delete('/admin/security/roles/Manager/users/test_manager', headers=oauth2Header(username), status=403)

    def test_access_to_security_settings(self):
        """
            Given i'm a Manager user
            When i try to interact with security endpoints
            Then i suceed
        """
        self.testapp.get('/admin/security', headers=oauth2Header(test_manager), status=200)
        self.testapp.get('/admin/security/users', headers=oauth2Header(test_manager), status=200)
        self.testapp.get('/admin/security/roles/Manager/users/test_manager', headers=oauth2Header(test_manager), status=200)
        self.testapp.post('/admin/security/roles/Manager/users/test_manager', headers=oauth2Header(test_manager), status=200)
        self.testapp.delete('/admin/security/roles/Manager/users/test_manager', headers=oauth2Header(test_manager), status=204)

