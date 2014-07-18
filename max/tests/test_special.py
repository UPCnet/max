# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header

from functools import partial
from mock import patch
from paste.deploy import loadapp

import os
import unittest


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

    def test_upload_and_get_profile_avatar(self):
        username = 'messi'
        self.create_user(username)
        thefile = open(os.path.join(os.path.dirname(__file__), "avatar.png"), "rb")
        files = [('image', 'avatar.png', thefile.read(), 'image/png')]

        res = self.testapp.post('/people/{}/avatar'.format(username), '', headers=oauth2Header(username), upload_files=files)
        self.assertEqual(res.status_code, 201)

        res = self.testapp.get('/people/{}/avatar'.format(username))
        self.assertEqual(res.status_code, 200)

    def tearDown(self):
        import pyramid.testing
        pyramid.testing.tearDown()
