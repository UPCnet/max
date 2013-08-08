# -*- coding: utf-8 -*-
import os
import json
import unittest
from functools import partial

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header, mock_post
from max.tests import test_manager, test_default_security


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

    def test_user_activities_stats(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)

        for i in range(11):
            self.create_activity(username, user_status)
        res = self.testapp.get('/people/%s/activities' % username, '', oauth2Header(username), status=200)
        self.assertEqual(len(res.json), 10)
        res = self.testapp.head('/people/%s/activities' % username, oauth2Header(username), status=200)
        self.assertEqual(res.headers.get('X-totalItems'), '11')

    def test_user_activities_stats_without_activity(self):
        username = 'messi'
        self.create_user(username)

        res = self.testapp.get('/people/%s/activities' % username, '', oauth2Header(username), status=200)
        self.assertEqual(len(res.json), 0)
        res = self.testapp.head('/people/%s/activities' % username, oauth2Header(username), status=200)
        self.assertEqual(res.headers.get('X-totalItems'), '0')

    def test_user_activities_stats_context_only(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)

        for i in range(11):
            self.create_activity(username, user_status)

        from .mockers import user_status_context
        from .mockers import create_context
        from .mockers import subscribe_context
        from hashlib import sha1

        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()

        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)

        res = self.testapp.head('/people/%s/activities?context=%s' % (username, url_hash), oauth2Header(username), status=200)
        self.assertEqual(res.headers.get('X-totalItems'), '1')

    def test_activities_stats_on_context(self):
        from .mockers import user_status_context
        from .mockers import create_context
        from .mockers import subscribe_context
        from hashlib import sha1

        username = 'messi'
        self.create_user(username)

        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context)

        for i in range(11):
            self.create_activity(username, user_status_context)

        res = self.testapp.get('/contexts/%s/activities' % (url_hash), '', oauth2Header(username), status=200)
        self.assertEqual(len(res.json), 10)

        res = self.testapp.head('/contexts/%s/activities' % (url_hash), oauth2Header(username), status=200)
        self.assertEqual(res.headers.get('X-totalItems'), '11')

    def test_global_activities_stats(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)

        for i in range(11):
            self.create_activity(username, user_status)
        res = self.testapp.get('/activities', '', oauth2Header(test_manager), status=200)
        self.assertEqual(len(res.json), 10)
        res = self.testapp.head('/activities', oauth2Header(test_manager), status=200)
        self.assertEqual(res.headers.get('X-totalItems'), '11')

    def test_global_comments_stats(self):
        from .mockers import user_status, user_comment
        username = 'messi'
        self.create_user(test_manager)
        self.create_user(username)

        for i in range(11):
            res = self.create_activity(username, user_status)
            self.testapp.post('/activities/%s/comments' % res.json['id'], json.dumps(user_comment), oauth2Header(username), status=201)
        res = self.testapp.get('/activities', '', oauth2Header(test_manager), status=200)
        self.assertEqual(len(res.json), 10)
        res = self.testapp.head('/activities/comments', oauth2Header(test_manager), status=200)
        self.assertEqual(res.headers.get('X-totalItems'), '11')

    def test_timeline_authors(self):
        """
            As a plain user
            When i query the last eight authors that appear in my timeline
            Then I get a list of persons
            And I'm in that list
        """
        from .mockers import user_status_context
        from .mockers import create_context
        from .mockers import subscribe_context

        self.create_context(create_context)

        # Create 20 users and subscribe to context
        for i in range(20):
            self.create_user('user-{}'.format(i))
            self.admin_subscribe_user_to_context('user-{}'.format(i), subscribe_context)

        # Create 2 consecutive activities for each user (backwards)
        # The last user to post will be the first-created user
        for usern in range(20)[::-1]:
            for count in range(2):
                self.create_activity('user-{}'.format(usern), user_status_context)

        res = self.testapp.get('/people/{}/timeline/authors'.format('user-0'), '', oauth2Header('user-0'), status=200)
        self.assertEqual(len(res.json), 8)
        self.assertEqual(res.json[0]['username'], 'user-0')
        self.assertEqual(res.json[7]['username'], 'user-7')

    def test_timeline_authors_not_enough(self):
        """
            As a plain user
            When i query the last eight authors that appear in my timeline
            Then I get a list of persons
            And that list is smaller than the minimum expected
            And I'm in that list
        """
        from .mockers import user_status_context
        from .mockers import create_context
        from .mockers import subscribe_context

        self.create_context(create_context)

        # Create 20 users and subscribe to context
        for i in range(3):
            self.create_user('user-{}'.format(i))
            self.admin_subscribe_user_to_context('user-{}'.format(i), subscribe_context)

        # Create 2 consecutive activities for each user (backwards)
        # The last user to post will be the first-created user
        for usern in range(3)[::-1]:
            for count in range(2):
                self.create_activity('user-{}'.format(usern), user_status_context)

        res = self.testapp.get('/people/{}/timeline/authors'.format('user-0'), '', oauth2Header('user-0'), status=200)
        self.assertEqual(len(res.json), 3)
        self.assertEqual(res.json[0]['username'], 'user-0')
        self.assertEqual(res.json[2]['username'], 'user-2')

    def test_context_authors(self):
        """
            As a plain user
            When i query the last eight authors that published in a context
            Then I get a list of persons
            And I am in that list
        """

        from .mockers import user_status_context
        from .mockers import create_context
        from .mockers import subscribe_context
        from hashlib import sha1

        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()

        # Create 20 users and subscribe to context
        # The last user to post will be the first-created user
        for i in range(20):
            self.create_user('user-{}'.format(i))
            self.admin_subscribe_user_to_context('user-{}'.format(i), subscribe_context)

        # Create 2 consecutive activities for each user
        for usern in range(20)[::-1]:
            for count in range(2):
                self.create_activity('user-{}'.format(usern), user_status_context)

        res = self.testapp.get('/contexts/{}/activities/authors'.format(url_hash), '', oauth2Header('user-0'), status=200)
        self.assertEqual(len(res.json), 8)
        self.assertEqual(res.json[0]['username'], 'user-0')
        self.assertEqual(res.json[7]['username'], 'user-7')

    def test_context_authors_not_enough(self):
        """
            As a plain user
            When i query the last eight authors that published in a context
            Then I get a list of persons
            And that list is smaller than the minimum expected
            And I am in that list
        """

        from .mockers import user_status_context
        from .mockers import create_context
        from .mockers import subscribe_context
        from hashlib import sha1

        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()

        # Create 20 users and subscribe to context
        # The last user to post will be the first-created user
        for i in range(3):
            self.create_user('user-{}'.format(i))
            self.admin_subscribe_user_to_context('user-{}'.format(i), subscribe_context)

        # Create 2 consecutive activities for each user
        for usern in range(3)[::-1]:
            for count in range(2):
                self.create_activity('user-{}'.format(usern), user_status_context)

        res = self.testapp.get('/contexts/{}/activities/authors'.format(url_hash), '', oauth2Header('user-0'), status=200)
        self.assertEqual(len(res.json), 3)
        self.assertEqual(res.json[0]['username'], 'user-0')
        self.assertEqual(res.json[2]['username'], 'user-2')

    def test_context_authors_not_subscribed(self):
        """
            As a plain user
            When i query the last eight authors that published in a context
            And i'm not subscribed to that context
            Then I get an error
        """
        from .mockers import create_context
        from hashlib import sha1

        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()

        username = 'messi'
        self.create_user(username)

        self.testapp.get('/contexts/{}/activities/authors'.format(url_hash), '', oauth2Header(username), status=401)
