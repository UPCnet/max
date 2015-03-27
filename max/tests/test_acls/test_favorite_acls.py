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

import json
import os
import unittest


class ActivitiesACLTests(unittest.TestCase, MaxTestBase):

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

    # Favorite activities tests

    def test_favorite(self):
        """
            Given i'm a regular user
            When i try to favorite an activity
            I succeed
        """
        from max.tests.mockers import user_status
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username_not_me), status=201)

    def test_favorite_impersonate(self):
        """
            Given i'm a regular user
            When i try to favorite an activity impersonated as another user
            I get a Forbidden Exception
        """
        from max.tests.mockers import user_status
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        impersonated_actor = {'actor': {'objectType': 'person', 'username': username}}
        self.testapp.post('/activities/%s/favorites' % activity_id, json.dumps(impersonated_actor), oauth2Header(username_not_me), status=403)

    def test_favorite_impersonate_as_manager(self):
        """
            Given i'm a Manager user
            When i try to favorite an activity impersonated as another user
            I get a Forbidden Exception
        """
        from max.tests.mockers import user_status
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        impersonated_actor = {'actor': {'objectType': 'person', 'username': username}}
        self.testapp.post('/activities/%s/favorites' % activity_id, json.dumps(impersonated_actor), oauth2Header(test_manager), status=201)

    # Unfavorite activities tests

    def test_unfavorite(self):
        """
            Given i'm a regular user
            When i try to unfavorite an activity
            I succeed
        """
        from max.tests.mockers import user_status
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username_not_me), status=201)
        self.testapp.delete('/activities/%s/favorites/%s' % (activity_id, username_not_me), '', oauth2Header(username_not_me), status=200)

    def test_unfavorite_impersonate(self):
        """
            Given i'm a regular user
            When i try to unfavorite an activity imperonsated as another user
            I get a Forbidden Exception
        """
        from max.tests.mockers import user_status
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username_not_me), status=201)
        self.testapp.delete('/activities/%s/favorites/%s' % (activity_id, username_not_me), '', oauth2Header(username), status=403)

    def test_unfavorite_impersonate_as_manager(self):
        """
            Given i'm a Manager user
            When i try to un unfavorite an activity impersonated as another user
            I succeed
        """
        from max.tests.mockers import user_status
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username_not_me), status=201)
        self.testapp.delete('/activities/%s/favorites/%s' % (activity_id, username_not_me), '', oauth2Header(test_manager), status=200)

    def test_unfavorite_not_favorited(self):
        """
            Given i'm a regular user
            When i try to unfavorite an activity
            And the activity is not favorited yet
            I get a Forbidden Exception
        """
        from max.tests.mockers import user_status
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.delete('/activities/%s/favorites/%s' % (activity_id, username_not_me), '', oauth2Header(username_not_me), status=403)
