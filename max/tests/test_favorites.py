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

    def test_favorite_activity(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           Then someone else can favorite this activity
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username_not_me), status=201)
        activity = self.testapp.get('/activities/%s' % activity_id, '', oauth2Header(username), status=200)

        self.assertEqual(res.json['object']['favorites'][0]['username'], username_not_me)
        self.assertEqual(res.json['object']['favorited'], True)
        self.assertEqual(res.json['object']['favoritesCount'], 1)

        self.assertEqual(activity.json['favorites'][0]['username'], username_not_me)
        self.assertEqual(activity.json['favorited'], False)
        self.assertEqual(activity.json['favoritesCount'], 1)

    def test_favorite_already_favorited_activity(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           And someone favorites this activity
           Then this someone else can't favorite twice this activity
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username_not_me), status=201)
        res = self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username_not_me), status=200)

        self.assertEqual(res.json['object']['favorites'][0]['username'], username_not_me)
        self.assertEqual(res.json['object']['favorited'], True)
        self.assertEqual(res.json['object']['favoritesCount'], 1)

    def test_unfavorite_activity(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           Then someone else can remove previously favorite mark from this activity
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username_not_me), status=201)
        res = self.testapp.delete('/activities/%s/favorites/%s' % (activity_id, username_not_me), '', oauth2Header(username_not_me), status=200)
        activity = self.testapp.get('/activities/%s' % activity_id, '', oauth2Header(username), status=200)

        self.assertEqual(res.json['object']['favorites'], [])
        self.assertEqual(res.json['object']['favorited'], False)
        self.assertEqual(res.json['object']['favoritesCount'], 0)

        self.assertEqual(activity.json['favorites'], [])
        self.assertEqual(activity.json['favorited'], False)
        self.assertEqual(activity.json['favoritesCount'], 0)

    def test_favorite_activity_by_various(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           Then someone else can favorite this activity
           and i also can favorite it
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username_not_me), status=201)
        res = self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username), status=201)

        self.assertEqual(res.json['object']['favorites'][0]['username'], username_not_me)
        self.assertEqual(res.json['object']['favorites'][1]['username'], username)
        self.assertEqual(res.json['object']['favorited'], True)
        self.assertEqual(res.json['object']['favoritesCount'], 2)

    def test_unfavorite_activity_get_other_favorites(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           And varius users favorite it
           And someone unfavorite it
           Then someone who unfavorite this activity
           and the rest of favorites remains
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username_not_me), status=201)
        res = self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username), status=201)
        res = self.testapp.delete('/activities/%s/favorites/%s' % (activity_id, username_not_me), '', oauth2Header(username_not_me), status=200)

        self.assertEqual(res.json['object']['favorites'][0]['username'], username)
        self.assertEqual(res.json['object']['favorited'], False)
        self.assertEqual(res.json['object']['favoritesCount'], 1)
