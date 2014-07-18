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
