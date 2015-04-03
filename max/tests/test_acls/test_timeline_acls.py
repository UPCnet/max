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


class TimelineACLTests(unittest.TestCase, MaxTestBase):

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

    # View user timeline

    def test_get_timeline(self):
        """
            Given i'm a regular user
            When i try to get my timeline
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        self.testapp.get('/people/%s/timeline' % username, '', oauth2Header(username), status=200)

    def test_get_timeline_as_manager(self):
        """
            Given i'm a Manager user
            When i try to get another user's timeline
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        self.testapp.get('/people/%s/timeline' % username, '', oauth2Header(test_manager), status=200)

    def test_get_timeline_as_other(self):
        """
            Given i'm a regular user
            When i try to get another user's timeline
            I get a Forbidden Exception
        """
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)

        self.testapp.get('/people/%s/timeline' % username, '', oauth2Header(other), status=403)

    # View user timeline authors

    def test_get_timeline_authors(self):
        """
            Given i'm a regular user
            When i try to get my timeline authors
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        self.testapp.get('/people/%s/timeline/authors' % username, '', oauth2Header(username), status=200)

    def test_get_timeline_authors_as_manager(self):
        """
            Given i'm a Manager user
            When i try to get another user's timeline authors
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        self.testapp.get('/people/%s/timeline/authors' % username, '', oauth2Header(test_manager), status=200)

    def test_get_timeline_authors_as_other(self):
        """
            Given i'm a regular user
            When i try to get another user's timeline authors
            I get a Forbidden Exception
        """
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)

        self.testapp.get('/people/%s/timeline/authors' % username, '', oauth2Header(other), status=403)
