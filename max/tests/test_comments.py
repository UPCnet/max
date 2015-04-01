# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header

from copy import deepcopy
from functools import partial
from mock import patch
from paste.deploy import loadapp

import json
import os
import unittest


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.reset_database(self.app)
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)

    # BEGIN TESTS

    def test_get_deletable_mark_for_own_comment(self):
        """
        """
        pass

    def test_get_deletable_mark_for_others_comment_in_own_activity(self):
        """
        """
        pass

    def test_get_deletable_mark_for_others_comment_in_others_activity(self):
        """
        """
        pass

    def test_post_comment_timeline(self):
        """ doctest .. http:post:: /activities/{activity}/comments """
        from .mockers import user_status, user_comment
        username = 'messi'
        self.create_user(username)
        activity = self.create_activity(username, user_status)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)
        result = res.json
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'comment')
        self.assertEqual(result.get('object', None).get('inReplyTo', None)[0].get('id'), str(activity.get('id')))

    def test_post_comment_on_context(self):
        """ doctest .. http:post:: /activities/{activity}/comments """
        from .mockers import user_status_context, user_comment
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity = self.create_activity(username, user_status_context)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)
        result = res.json
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'comment')
        self.assertEqual(result.get('object', None).get('inReplyTo', None)[0].get('id'), str(activity.get('id')))

    def test_get_comments(self):
        """ doctest .. http:get:: /activities/{activity}/comments """
        from .mockers import user_status, user_comment
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity = self.create_activity(username, user_status)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)
        res = self.testapp.get('/activities/%s/comments' % str(activity.get('id')), "", oauth2Header(username), status=200)
        result = res.json
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[0].get('objectType', None), 'comment')

    def test_get_comments_for_user(self):
        """
            Test get all comments for a user, both timeline and context
        """
        from .mockers import user_status, user_comment
        from .mockers import subscribe_context, create_context, user_status_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)

        activity = self.create_activity(username, user_status)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)

        activity2 = self.create_activity(username, user_status_context)
        activity2 = activity2.json
        res = self.testapp.post('/activities/%s/comments' % str(activity2.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)

        res = self.testapp.get('/people/%s/comments' % username, "", oauth2Header(username), status=200)
        result = res.json
        self.assertEqual(len(result), 2)

        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[0].get('verb', None), 'comment')
        self.assertEqual(result[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[1].get('verb', None), 'comment')

    def test_delete_own_comment(self):
        """
            Given i'm plain user
            When i comment an activity
            Then i can delete it
        """
        from .mockers import user_status, user_comment
        username = 'messi'
        self.create_user(username)
        activity = self.create_activity(username, user_status)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)
        comment_id = res.json['id']
        res = self.testapp.delete('/activities/%s/comments/%s' % (str(activity.get('id')), comment_id), '', oauth2Header(username), status=204)

    def test_delete_others_comment_in_own_activity(self):
        """
            Given i'm a plain user
            When someone else commments on an activity of mine
            Then I can delete it, 'cause the activity is mine
        """
        from .mockers import user_status, user_comment
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)

        activity = self.create_activity(username, user_status)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username_not_me), status=201)
        comment_id = res.json['id']
        res = self.testapp.delete('/activities/%s/comments/%s' % (str(activity.get('id')), comment_id), '', oauth2Header(username), status=204)

    def test_delete_others_comment_in_others_activity(self):
        """
            Given i'm a plain user
            When someone else comments on someone else's activity
            Then i can't delete it
        """
        from .mockers import user_status, user_comment
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        activity = self.create_activity(username_not_me, user_status)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username_not_me), status=201)
        comment_id = res.json['id']
        res = self.testapp.delete('/activities/%s/comments/%s' % (str(activity.get('id')), comment_id), '', oauth2Header(username), status=403)
