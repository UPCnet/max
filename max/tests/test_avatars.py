# -*- coding: utf-8 -*-
from max.tests import test_cloudapis
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxAvatarsTestBase
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import MockTweepyAPI
from max.tests.base import mock_get
from max.tests.base import mock_post
from max.tests.base import oauth2Header
from max.utils.image import get_avatar_folder

from functools import partial
from mock import patch
from paste.deploy import loadapp

import httpretty
import json
import os
import shutil
import tempfile
import unittest


def http_mock_twitter_user_image(image):
    httpretty.register_uri(
        httpretty.GET, "https://pbs.twimg.com/profile_images/1901828730/logo_MAX_color_normal.png",
        body=open(image, "rb").read(),
        status=200,
        content_type="image/png"
    )


class AvatarFolderTests(unittest.TestCase, MaxTestBase):
    """
        Tests to check the correct resoultion of avatar folder
        for different scenarios.
    """

    def setUp(self):
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.folder)

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

        expected_folder = '{}/people/sh'.format(self.folder)

        self.assertEqual(folder, expected_folder)
        self.assertFileExists(expected_folder)

    def test_avatar_folder_with_context_and_id_2(self):
        """
            Given a base folder
            And a context and identifier
            Then the first subfolder contains the context
            And the second subfolder the trimmed identifier correspondint to the context
        """
        folder = get_avatar_folder(self.folder, 'contexts', 'e6847aed3105e85ae603c56eb2790ce85e212997')

        expected_folder = '{}/contexts/e6/84/7a'.format(self.folder)

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

        expected_folder = '{}/people/large/sh'.format(self.folder)

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


class AvatarTests(unittest.TestCase, MaxTestBase, MaxAvatarsTestBase):
    """
        Tests to check the uploading, downlading and retrieving of all
        avatar types used in max, included the ones coming from twitter.
    """

    def setUp(self):
        self.conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=self.conf_dir)
        self.reset_database(self.app)
        self.app.registry.max_store.security.insert(test_default_security)
        self.app.registry.max_store.cloudapis.insert(test_cloudapis)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.patched_get = patch('requests.get', new=partial(mock_get, self))
        self.patched_get.start()

        self.testapp = MaxTestApp(self)
        self.create_user(test_manager)

        MaxAvatarsTestBase.setUp(self)

    def tearDown(self):
        """
            Deletes test avatar folder with all test images
        """
        self.patched_post.stop()
        self.patched_get.stop()
        MaxAvatarsTestBase.tearDown(self)

    # BEGIN TESTS

    def test_upload_user_avatar(self):
        """
            Given a user without avatar
            When I upload an image for that user
            Then a normal 48x48 image is stored in the correct avatar folder
            And a large 250x250 image is stored in the correct avatar folder
        """
        username = 'messi'
        self.create_user(username)
        avatar_file = open(os.path.join(self.conf_dir, "avatar.png"), "rb")
        files = [('image', 'avatar.png', avatar_file.read(), 'image/png')]

        self.testapp.post('/people/{}/avatar'.format(username), '', headers=oauth2Header(username), upload_files=files, status=201)

        self.assertEqual(self.get_user_avatar_dimensions(username), (48, 48))
        self.assertEqual(self.get_user_avatar_dimensions(username, 'large'), (250, 250))

    def test_get_user_avatar(self):
        """
            Given a user with avatar
            When I retrieve the avatar
            Then I get the 48x48 version of that avatar
        """
        username = 'messi'
        self.create_user(username)
        self.upload_user_avatar(username, "avatar.png")

        response = self.testapp.get('/people/%s/avatar' % username, '', {}, status=200)

        self.assertIn('image', response.content_type)
        self.assertEqual(self.get_image_dimensions_from(response), (48, 48))

    def test_get_user_avatar_large(self):
        """
            Given a user without avatar
            When I retrieve the large avatar
            Then I get the 250x250 version of that avatar
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
            Given a context with twitter username
            When i retrieve the context's avatar
            Then the twitter's user avatar is downloaded and stored
        """
        from hashlib import sha1
        from .mockers import create_context_full

        avatar_image = os.path.join(self.conf_dir, "avatar.png")
        http_mock_twitter_user_image(avatar_image)

        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()

        response = self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)

        self.assertEqual(self.get_image_dimensions_from(response), (98, 98))
        avatar_folder = get_avatar_folder(self.avatar_folder, 'contexts', url_hash)
        self.assertFileExists(os.path.join(avatar_folder, url_hash))

    @httpretty.activate
    @patch('tweepy.API', new=partial(MockTweepyAPI, fail=True))
    def test_get_context_twitter_download_error_from_twitter_avatar(self):
        """
            Given a context with twitter username
            When i retrieve the context's avatar
            And some error happens when talking to twitter
            Then the twitter's user avatar is not downloaded nor stored
            And the default image is retrieved
        """
        from hashlib import sha1
        from .mockers import create_context_full

        avatar_image = os.path.join(self.conf_dir, "avatar.png")
        http_mock_twitter_user_image(avatar_image)

        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()

        response = self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)

        self.assertEqual(self.get_image_dimensions_from(response), (48, 48))
        self.assertFileNotExists(os.path.join(self.avatar_folder, '{}.png'.format(url_hash)))

    def test_get_context_twitter_avatar_inexistent_context(self):
        """
            Given an unexisting context
            When i retrieve the context's avatar
            Then i get a NotFound error
            And no image is retrieved
        """
        self.testapp.get('/contexts/%s/avatar' % '000000000000000000', '', {}, status=404)

    @httpretty.activate
    @patch('tweepy.API', MockTweepyAPI)
    def test_get_context_twitter_avatar_already_downloaded(self):
        """
            Given a context with twitter username
            When i retrieve the context's avatar
            And the image has just been retrieved
            Then the twitter's user avatar is not downloaded again
            And the existing image is returned
        """
        from hashlib import sha1
        from .mockers import create_context_full

        avatar_image = os.path.join(self.conf_dir, "avatar.png")
        http_mock_twitter_user_image(avatar_image)

        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()

        self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)
        old_mod_date = self.get_context_avatar_modification_time(url_hash)

        self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)
        new_mod_date = self.get_context_avatar_modification_time(url_hash)

        self.assertEqual(old_mod_date, new_mod_date)

    @httpretty.activate
    @patch('tweepy.API', MockTweepyAPI)
    def test_get_context_twitter_avatar_redownload_previous(self):
        """
            Given a context with twitter username
            When i retrieve the context's avatar
            And the image has not been retrieved for at least 4 hours
            Then the twitter's user avatar is redownloaded
            And the new image is returned
        """
        from hashlib import sha1
        from .mockers import create_context_full

        avatar_image = os.path.join(self.conf_dir, "avatar.png")
        http_mock_twitter_user_image(avatar_image)

        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()

        self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)
        self.rewind_context_avatar_mod_time(url_hash, hours=4)
        rewinded_mod_date = self.get_context_avatar_modification_time(url_hash)

        self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)
        new_mod_date = self.get_context_avatar_modification_time(url_hash)

        self.assertNotEqual(rewinded_mod_date, new_mod_date)
