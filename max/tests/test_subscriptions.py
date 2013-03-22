# -*- coding: utf-8 -*-
import os
import json
import unittest
from hashlib import sha1

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, oauth2Header
from max.tests import test_manager, test_default_security


class mock_post(object):

    def __init__(self, *args, **kwargs):
        pass

    text = ""
    status_code = 200


@patch('requests.post', new=mock_post)
class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        from webtest import TestApp
        self.testapp = TestApp(self.app)

    # BEGIN TESTS

    def test_subcribe_to_restricted_context_as_plain_user(self):
        """
            Create a restricted join context, then check that a plain user cannot subscribe himself to it
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        self.subscribe_to_context(username, subscribe_context, expect=401)

    def test_subscribe_to_public_context_as_plain_user(self):
        """
            Create a public join context, then check that a plain user can subscribe himself to it
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', join='public', invite='restricted'))
        self.user_subscribe_to_context(username, subscribe_context, expect=200)

    def test_list_all_public_subcribtable_contexts(self):
        """
            Create one public context and a restricted one, then list the contexts filtered by join permission=public
        """
        from .mockers import create_context, create_contextA
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', join='public', invite='restricted'))
        self.create_context(create_contextA, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        res = self.testapp.get('/contexts/public' % username, {}, oauth2Header(username), status=200)
        result = json.loads(res.text)

    def test_unsubscribe_from_restricted_context_as_plain_user(self):
        """
            Create a restricted context, make admin subscribe the user, user fails to removes subscription
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        self.subscribe_to_context(username, subscribe_context, expect=200)
        url_hash = sha1(create_context['object']['url']).hexdigest()
        res = self.testapp.delete('/people/%s/subscriptions/%s' % (username, url_hash), {}, oauth2Header(username), status=401)
        result = json.loads(res.text)

    def test_unsubscribe_from_restricted_context_as_admin(self):
        """
            Create a restricted context, make admin subscribe the user, admin successfully removes subscription
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        self.subscribe_to_context(username, subscribe_context, expect=200)
        res = self.testapp.delete('/admin/people/%s/subscriptions/%s' % (username, url_hash), {}, oauth2Header(username), status=200)

    def test_unsubscribe_from_public_context_as_plain_user(self):
        """
            Create a restricted context, user subscribes himself, user successfully removes subscription
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        self.user_subscribe_to_context(username, subscribe_context, expect=200)
        self.user_unsubscribe_from_context(username, subscribe_context, expect=200)

    def test_unsubscribe_from_public_context_as_admin(self):
        """
            Create a restricted context, user subscribes himself, admin succesfully removes subscription
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        self.user_subscribe_to_context(username, subscribe_context, expect=200)
        self.unsubscribe_from_context(username, subscribe_context, expect=200)

    def test_change_public_context_to_restricted(self):
        """
            Create a public context, user subscribes to context.
            Change the context to join=restricted, and user fails to remove his subscription
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', join='public', invite='restricted'))
        self.user_subscribe_to_context(username, subscribe_context, expect=200)
        self.user_unsubscribe_user_from_context(username, subscribe_context, expect=401)

    def test_change_restricted_context_to_public(self):
        """
            Create a restricted context, admin subscribes the user to context.
            Change the context to join=public, and user successfully removes himself from context
        """
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        self.subscribe_to_context(username, subscribe_context, expect=200)
        self.user_unsubscribe_user_from_context(username, subscribe_context, expect=200)





