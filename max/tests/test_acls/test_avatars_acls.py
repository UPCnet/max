# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import MaxAvatarsTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header
from max.rest.utils import get_avatar_folder

from max.tests.test_avatars import http_mock_twitter_user_image
from functools import partial
from mock import patch
from paste.deploy import loadapp

import json
import os
import unittest


class AvatarsACLTests(unittest.TestCase, MaxTestBase, MaxAvatarsTestBase):

    def setUp(self):
        self.conf_dir = os.path.dirname(os.path.dirname(__file__))

        self.app = loadapp('config:tests.ini', relative_to=self.conf_dir)
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

        MaxAvatarsTestBase.setUp(self)

    def tearDown(self):
        """
            Deletes test avatar folder with all test images
        """
        self.patched_post.stop()
        MaxAvatarsTestBase.tearDown(self)

    # Add person avatar tests

    def test_add_user_avatar(self):
        """
            Given i'm a regular user
            When i try to update my avatar
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        avatar_file = open(os.path.join(self.conf_dir, "avatar.png"), "rb")
        files = [('image', 'avatar.png', avatar_file.read(), 'image/png')]

        self.testapp.post('/people/{}/avatar'.format(username), '', headers=oauth2Header(username), upload_files=files, status=201)

    def test_add_user_avatar_as_manager(self):
        """
            Given i'm a regular user
            When i try to update my avatar
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        avatar_file = open(os.path.join(self.conf_dir, "avatar.png"), "rb")
        files = [('image', 'avatar.png', avatar_file.read(), 'image/png')]

        self.testapp.post('/people/{}/avatar'.format(username), '', headers=oauth2Header(test_manager), upload_files=files, status=201)

    def test_add_other_user_avatar(self):
        """
            Given i'm a regular user
            When i try to update another user's avatar
            I get a Forbidden Exception
        """
        username = 'sheldon'
        self.create_user(username)
        other = 'penny'
        self.create_user(other)
        avatar_file = open(os.path.join(self.conf_dir, "avatar.png"), "rb")
        files = [('image', 'avatar.png', avatar_file.read(), 'image/png')]

        self.testapp.post('/people/{}/avatar'.format(username), '', headers=oauth2Header(other), upload_files=files, status=403)

    # Get person avatar tests, Large avatars acl's are not tested as is the same endpoint

    def test_get_user_avatar_unauthenticated(self):
        """
            Given i'm a unauthenticated user
            When I try to get a user avatar
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        self.upload_user_avatar(username, "avatar.png")
        self.testapp.get('/people/%s/avatar' % username, '', {}, status=200)

    # Get twitter avatar tests

    def test_get_twitter_avatar_unauthenticated(self):
        """
            Given i'm a unauthenticated user
            When I try to get a context avatar coming from twitter
            I succeed
        """
        from hashlib import sha1
        from .mockers import create_context_full

        avatar_image = os.path.join(self.conf_dir, "avatar.png")
        http_mock_twitter_user_image(avatar_image)

        self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()

        self.testapp.get('/contexts/%s/avatar' % url_hash, '', {}, status=200)
