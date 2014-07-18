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

    def test_create_context_with_notifications(self):
        """ doctests .. http:post:: /contexts"""
        from .mockers import create_context_post_notifications as create_context
        new_context = dict(create_context)
        res = self.testapp.post('/contexts', json.dumps(new_context), oauth2Header(test_manager), status=201)
        self.assertEqual(res.json['notifications'], 'posts')

    def test_delete_context_with_notifications_removes_subscriptions(self):
        """
        """
        from .mockers import subscribe_context
        from .mockers import create_context_post_notifications as create_context
        from .mockers import user_status_context
        from hashlib import sha1

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)

        url_hash = sha1(create_context['url']).hexdigest()
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)

        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')
        self.assertEqual(len(result.get('subscribedTo', [])), 0)

        return url_hash

    def test_subscribe_user_to_context_with_notifications(self):
        """
        """
        from .mockers import create_context_post_notifications as create_context
        from .mockers import subscribe_context
        from hashlib import sha1

        username = 'messi'
        url_hash = sha1(create_context['url']).hexdigest()

        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', subscribe='restricted', invite='restricted'))
        self.testapp.post('/people/%s/subscriptions' % username, json.dumps(subscribe_context), oauth2Header(test_manager), status=201)
        res = self.testapp.get('/people/%s/subscriptions' % username, json.dumps(subscribe_context), oauth2Header(username), status=200)

        self.assertEqual(res.json[0]['notifications'], 'posts')
        return url_hash, username

    def test_unsubscribe_user_from_context_with_notifications(self):
        """
        """
        from .mockers import create_context_post_notifications as create_context
        from .mockers import subscribe_context
        from hashlib import sha1

        username = 'messi'
        url_hash = sha1(create_context['url']).hexdigest()

        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', subscribe='restricted', invite='restricted'))
        self.testapp.post('/people/%s/subscriptions' % username, json.dumps(subscribe_context), oauth2Header(test_manager), status=201)
        res = self.testapp.delete('/people/%s/subscriptions/%s' % (username, url_hash), {}, oauth2Header(test_manager), status=204)

        res = self.testapp.get('/people/%s/subscriptions' % username, json.dumps(subscribe_context), oauth2Header(username), status=200)

        self.assertEqual(len(res.json), 0)
        return url_hash, username

    def test_post_activity_on_context_with_notifications(self):
        """ Post an activity to a context which needs the user to be subscribed to read and write
            and we have previously subscribed the user.
        """
        from .mockers import subscribe_context
        from .mockers import create_context_post_notifications as create_context
        from .mockers import user_status_context
        from hashlib import sha1

        username = 'messi'
        url_hash = sha1(create_context['url']).hexdigest()

        self.create_user(username)
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_context, permissions=context_permissions)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)

        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], subscribe_context['object']['url'])
        self.assertEqual(result.get('contexts', None)[0]['notifications'], 'posts')

        return url_hash, username, user_status_context

    def test_post_comment_with_comments_notification(self):
        """ doctest .. http:post:: /activities/{activity}/comments """
        from .mockers import user_status_context, user_comment
        from .mockers import subscribe_context
        from .mockers import create_context_comments_notifications as create_context
        from hashlib import sha1

        username = 'messi'
        url_hash = sha1(create_context['url']).hexdigest()

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

        return url_hash, username, user_status_context, user_comment
