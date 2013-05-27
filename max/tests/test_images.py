# -*- coding: utf-8 -*-
import os
import unittest
from functools import partial

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, MaxTestApp, mock_post
from max.tests import test_default_security
from max.tests.mock_image import image


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
        if not os.path.exists(self.app.registry.settings['avatar_folder']):
            os.mkdir(self.app.registry.settings['avatar_folder'])
            open('%s/missing.jpg' % self.app.registry.settings['avatar_folder'], 'w').write(image)

    # BEGIN TESTS

    def test_get_image(self):
        """
        """
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/people/%s/avatar' % username, '', {}, status=200)
        self.assertIn('image', res.content_type)
        self.assertEqual(len(image), len(res.body))
