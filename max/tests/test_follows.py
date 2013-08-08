# -*- coding: utf-8 -*-
import os
import unittest
from functools import partial

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header, mock_post
from max.tests import test_default_security


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

    # BEGIN TESTS

    def test_follow_user(self):
        """
        """
        username = 'messi'
        username2 = 'xavi'

        self.create_user(username)
        self.create_user(username2)

        res = self.testapp.post('/people/%s/follows/%s' % (username, username2), '', oauth2Header(username), status=201)
        self.assertEqual(res.json['verb'], 'follow')

        res = self.testapp.get('/people/%s' % (username), '', oauth2Header(username), status=200)
        self.assertEqual(username2, res.json['following'][0]['username'])

    def test_user_sees_followed_activity(self):
        """
        """
        from .mockers import user_status

        username = 'messi'
        username2 = 'xavi'

        self.create_user(username)
        self.create_user(username2)

        self.create_activity(username, user_status)
        self.create_activity(username2, user_status)

        res = self.testapp.post('/people/%s/follows/%s' % (username, username2), '', oauth2Header(username), status=201)
        self.assertEqual(res.json['verb'], 'follow')

        res = self.testapp.get('/people/%s/timeline' % (username), '', oauth2Header(username), status=200)
        self.assertEqual(len(res.json), 2)


    # IMPORTANT !!!!!!!!!!!!!!!!

    # Test when user follows user2, and user2 is subscribed to contexts that user1 is not. User
    # should not be able to read user2 activity in non-subscribed contexts. We'll have to enchance
    # the query on max.rest.timeline.timelineQuery
