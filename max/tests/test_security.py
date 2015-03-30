# -*- coding: utf-8 -*-
from max.tests import test_default_security_single
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
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('messages')
        self.app.registry.max_store.security.insert(test_default_security_single)
        self.app.registry.max_security = test_default_security_single
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)

    def test_get_security(self):
        res = self.testapp.get('/admin/security', "", oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('roles', None).get('Manager')[0], 'test_manager')

    def test_security_add_user_to_role(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=201)
        self.assertListEqual(['messi', 'test_manager'], res.json)

    def test_security_add_user_to_non_allowed_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('WrongRole', username), "", oauth2Header(test_manager), status=400)

    def test_security_remove_user_from_non_allowed_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.delete('/admin/security/roles/%s/users/%s' % ('WrongRole', username), "", oauth2Header(test_manager), status=400)

    def test_security_add_user_to_role_already_has_role(self):
        res = self.testapp.post('/admin/security/roles/%s/users/%s' % ('Manager', 'test_manager'), "", oauth2Header(test_manager), status=200)
        self.assertListEqual(['test_manager'], res.json)

    def test_security_remove_user_from_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=201)
        self.testapp.delete('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=204)

    def test_security_remove_user_from_role_user_not_in_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.delete('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=404)

    def test_security_add_user_to_role_check_security_reloaded(self):
        test_manager2 = 'messi'
        self.create_user(test_manager2)
        self.testapp.get('/activities', "", oauth2Header(test_manager2), status=403)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('Manager', test_manager2), "", oauth2Header(test_manager), status=201)
        self.testapp.get('/activities', "", oauth2Header(test_manager2), status=200)

    def test_security_remove_user_from_role_check_security_reloaded(self):
        test_manager2 = 'messi'
        self.create_user(test_manager2)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('Manager', test_manager2), "", oauth2Header(test_manager), status=201)
        self.testapp.get('/activities', "", oauth2Header(test_manager2), status=200)
        self.testapp.delete('/admin/security/roles/%s/users/%s' % ('Manager', test_manager2), "", oauth2Header(test_manager), status=204)
        self.testapp.get('/activities', "", oauth2Header(test_manager2), status=403)

