# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_get
from max.tests.base import mock_post
from max.tests.base import oauth2Header

from max.rest.utils import get_avatar_folder

from functools import partial
from mock import patch
from paste.deploy import loadapp

import httpretty
import json
import os
import shutil
import tempfile
import tweepy
import unittest

from io import BytesIO
from PIL import Image


def http_mock_twitter_user_image(image):
    httpretty.register_uri(
        httpretty.GET, "https://pbs.twimg.com/profile_images/1901828730/logo_MAX_color_normal.png",
        body=open(image, "rb").read(),
        status=200,
        content_type="image/png"
    )


class MockTweepyAPI(object):
    def __init__(self, auth):
        pass

    def verify_credentials(self, *args, **kwargs):
        return True

    def get_user(self, username):
        user = tweepy.models.User
        user.profile_image_url_https = 'https://pbs.twimg.com/profile_images/1901828730/logo_MAX_color_normal.png'
        user.id_str = '526326641'
        return user


class AvatarFolderTests(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.folder)

    def assertFileExists(self, path):
        self.assertTrue(os.path.exists(path))

    def test_avatar_folder_without_params(self):
        """
            Given a base folder
            And no extra params
            Then there are no subfolders
        """
        folder = get_avatar_folder(self.folder)

        expected_folder = self.folder

        self.assertEqual(folder, expected_folder)
        self.assertFileExists(expected_folder)

    def test_avatar_folder_with_context(self):
        """
            Given a base folder
            And a context with no extra params
            Then the subfolder contains the context
        """
        folder = get_avatar_folder(self.folder, 'people')

        expected_folder = '{}/people'.format(self.folder)

        self.assertEqual(folder, expected_folder)
        self.assertFileExists(expected_folder)

    def test_avatar_folder_with_context_and_id(self):
        """
            Given a base folder
            And a context and identifier
            Then the first subfolder contains the context
            And the second subfolder the trimmed identifier correspondint to the context
        """
        folder = get_avatar_folder(self.folder, 'people', 'sheldon')

        expected_folder = '{}/people/s'.format(self.folder)

        self.assertEqual(folder, expected_folder)
        self.assertFileExists(expected_folder)

    def test_avatar_folder_with_unknown_context_and_id(self):
        """
            Given a base folder
            And a context and identifier
            And there is no identifier splitter for that context
            Then the first subfolder contains the context
            And the identifier is not used

        """
        folder = get_avatar_folder(self.folder, 'unknown', 'sheldon')

        expected_folder = '{}/unknown'.format(self.folder)

        self.assertEqual(folder, expected_folder)
        self.assertFileExists(expected_folder)

    def test_avatar_folder_with_context_and_id_and_size(self):
        """
            Given a base folder
            And a context, identifier and size
            Then the first subfolder contains the context
            And the second subfolder contains the size
            And the third subfolder the trimmed identifier correspondint to the context
        """
        folder = get_avatar_folder(self.folder, 'people', 'sheldon', 'large')

        expected_folder = '{}/people/large/s'.format(self.folder)

        self.assertEqual(folder, expected_folder)
        self.assertFileExists(expected_folder)

    def test_avatar_folder_with_context_and_size(self):
        """
            Given a base folder
            And a context and size
            Then the first subfolder contains the context
            And the second subfolder contains the size
        """
        folder = get_avatar_folder(self.folder, 'people', size='large')

        expected_folder = '{}/people/large'.format(self.folder)

        self.assertEqual(folder, expected_folder)
        self.assertFileExists(expected_folder)


class AvatarTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        self.conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=self.conf_dir)
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

        self.avatar_folder = self.app.registry.settings['avatar_folder']

        if not os.path.exists(self.avatar_folder):  # pragma: no cover
            os.mkdir(self.avatar_folder)

        # Generate default avatar images
        shutil.copyfile('{}/missing.png'.format(self.conf_dir), '{}/missing.png'.format(self.avatar_folder))
        shutil.copyfile('{}/missing.png'.format(self.conf_dir), '{}/missing-people.png'.format(self.avatar_folder))
        shutil.copyfile('{}/missing.png'.format(self.conf_dir), '{}/missing-people-large.png'.format(self.avatar_folder))

    def tearDown(self):
        shutil.rmtree(self.avatar_folder)

    def get_image_dimensions_from(self, response):
        return Image.open(BytesIO(response.body)).size

    def get_user_avatar_dimensions(self, username, size=''):
        avatar_folder = get_avatar_folder(self.avatar_folder, 'people', username, size=size)
        return Image.open('{}/{}'.format(avatar_folder, username)).size

    def upload_user_avatar(self, username, filename):
        avatar_file = open(os.path.join(self.conf_dir, filename), "rb")
        files = [('image', filename, avatar_file.read(), 'image/png')]
        self.testapp.post('/people/{}/avatar'.format(username), '', headers=oauth2Header(username), upload_files=files, status=201)

    # BEGIN TESTS

    def test_upload_user_avatar(self):
        username = 'messi'
        self.create_user(username)
        avatar_file = open(os.path.join(self.conf_dir, "avatar.png"), "rb")
        files = [('image', 'avatar.png', avatar_file.read(), 'image/png')]

        self.testapp.post('/people/{}/avatar'.format(username), '', headers=oauth2Header(username), upload_files=files, status=201)

        self.assertEqual(self.get_user_avatar_dimensions(username), (48, 48))
        self.assertEqual(self.get_user_avatar_dimensions(username, 'large'), (250, 250))

    def test_get_user_avatar(self):
        """
        """
        username = 'messi'
        self.create_user(username)
        self.upload_user_avatar(username, "avatar.png")

        response = self.testapp.get('/people/%s/avatar' % username, '', {}, status=200)

        self.assertIn('image', response.content_type)
        self.assertEqual(self.get_image_dimensions_from(response), (48, 48))

    def test_get_user_avatar_large(self):
        """
        """
        username = 'messi'
        self.create_user(username)
        self.upload_user_avatar(username, "avatar.png")

        response = self.testapp.get('/people/%s/avatar/%s' % (username, 'large'), '', {}, status=200)

        self.assertIn('image', response.content_type)
        self.assertIn('image', response.content_type)
        self.assertEqual(self.get_image_dimensions_from(response), (250, 250))

    @httpretty.activate
    @patch('tweepy.API', MockTweepyAPI)
    def test_get_context_twitter_download_avatar(self):
        """
        """
        from hashlib import sha1
        from .mockers import create_context_full

        avatar_image = os.path.join(self.conf_dir, "avatar.png")
        http_mock_twitter_user_image(avatar_image)

        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()

        response = self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)

        self.assertEqual(self.get_image_dimensions_from(response), (98, 98))
        self.assertFileExists(os.path.join(self.conf_dir, ""))

    def test_get_context_twitter_download_error_from_twitter_avatar(self):
        """
        """
        from .mock_image import image
        from hashlib import sha1
        from .mockers import create_context_full
        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()

        response = self.testapp.get('/contexts/%s/avatar' % url_hash, '', {'SIMULATE_TWITTER_FAIL': '1'}, status=200)
        self.assertIn('image', response.content_type)
        self.assertEqual(len(image), len(response.body))
        self.assertEqual(len(os.listdir(self.app.registry.settings['avatar_folder'])), 1)

    def test_get_context_twitter_avatar_inexistent_context(self):
        """
        """
        self.testapp.get('/contexts/%s/avatar' % '000000000000000000', '', {}, status=404)

    def test_get_context_twitter_avatar_already_downloaded(self):
        """
        """
        from .mock_image import image
        from hashlib import sha1
        from .mockers import create_context_full
        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()
        open('%s/%s.png' % (self.app.registry.settings['avatar_folder'], url_hash), 'w').write(image)

        response = self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)
        self.assertIn('image', response.content_type)
        self.assertEqual(len(image), len(response.body))

    @unittest.skipUnless(os.environ.get('Twitter', False), 'Skipping due to lack of Twitter config')
    def test_get_context_twitter_avatar_redownload_previous(self):
        """
        """
        from hashlib import sha1
        from .mockers import create_context_full
        from .mock_image import image
        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()
        image_filename = '%s/%s.png' % (self.app.registry.settings['avatar_folder'], url_hash)

        # Save the file and rewind its date 4 hours
        open(image_filename, 'w').write(image)
        modification_time = os.path.getmtime(image_filename)
        new_time = modification_time - (60 * 60 * 4)
        os.utime(image_filename, (new_time, new_time))
        modification_time = os.path.getmtime(image_filename)

        response = self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)
        self.assertIn('image', response.content_type)
        self.assertEqual(len(image), len(response.body))

        # Assert that the file is rencently downloaded
        new_modification_time = os.path.getmtime(image_filename)
        self.assertNotEqual(modification_time, new_modification_time)
