# -*- coding: utf-8 -*-
import os
import unittest
import json
from functools import partial

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, MaxTestApp, mock_post, mock_get, oauth2Header
from max.tests import test_default_security, test_manager
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
        self.patched_get = patch('requests.get', new=partial(mock_get, self))
        self.patched_get.start()

        self.testapp = MaxTestApp(self)

        # Create folder and default avatar image
        if not os.path.exists(self.app.registry.settings['avatar_folder']):  # pragma: no cover
            os.mkdir(self.app.registry.settings['avatar_folder'])
        open('%s/missing.png' % self.app.registry.settings['avatar_folder'], 'w').write(image)

    def tearDown(self):
        for image in os.listdir(self.app.registry.settings['avatar_folder']):
            os.remove('%s/%s' % (self.app.registry.settings['avatar_folder'], image))
        os.rmdir(self.app.registry.settings['avatar_folder'])

    # BEGIN TESTS

    def test_get_user_avatar(self):
        """
        """
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/people/%s/avatar' % username, '', {}, status=200)
        self.assertIn('image', res.content_type)
        self.assertEqual(len(image), len(res.body))

    def test_get_context_twitter_download_avatar(self):
        """
        """
        from hashlib import sha1
        from .mockers import create_context_full
        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()

        res = self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)
        self.assertIn('image', res.content_type)
        self.assertEqual(len(image), len(res.body))

    def test_get_context_twitter_download_error_from_twitter_avatar(self):
        """
        """
        from hashlib import sha1
        from .mockers import create_context_full
        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()

        res = self.testapp.get('/contexts/%s/avatar' % url_hash, '', {'SIMULATE_TWITTER_FAIL': '1'}, status=200)
        self.assertIn('image', res.content_type)
        self.assertEqual(len(image), len(res.body))
        self.assertEqual(len(os.listdir(self.app.registry.settings['avatar_folder'])), 1)

    def test_get_context_twitter_avatar_inexistent_context(self):
        """
        """
        self.testapp.get('/contexts/%s/avatar' % '000000000000000000', '', {}, status=404)

    def test_get_context_twitter_avatar_already_downloaded(self):
        """
        """
        from hashlib import sha1
        from .mockers import create_context_full
        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()
        open('%s/%s.png' % (self.app.registry.settings['avatar_folder'], url_hash), 'w').write(image)

        res = self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)
        self.assertIn('image', res.content_type)
        self.assertEqual(len(image), len(res.body))

    def test_get_context_twitter_avatar_redownload_previous(self):
        """
        """
        from hashlib import sha1
        from .mockers import create_context_full
        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()
        image_filename = '%s/%s.png' % (self.app.registry.settings['avatar_folder'], url_hash)

        # Save the file and rewind its date 4 hours
        open(image_filename, 'w').write(image)
        modification_time = os.path.getmtime(image_filename)
        new_time = modification_time - (60 * 60 * 4)
        os.utime(image_filename, (new_time, new_time))
        modification_time = os.path.getmtime(image_filename)

        res = self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)
        self.assertIn('image', res.content_type)
        self.assertEqual(len(image), len(res.body))

        # Assert that the file is rencently downloaded
        new_modification_time = os.path.getmtime(image_filename)
        self.assertNotEqual(modification_time, new_modification_time)
