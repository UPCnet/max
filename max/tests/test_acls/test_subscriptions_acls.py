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

from hashlib import sha1


class SubscriptionsACLTests(unittest.TestCase, MaxTestBase):

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

    # Create subscription tests

    def test_subscribe_user_to_context_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to get subscribe another user to a context
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'

        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)

    def test_subscribe_user_to_context_as_context_owner(self):
        """
            Given i'm a user that doesn't have the Manager role
            And i'm the owner of the context
            When i try to subscribe another user to a context
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'

        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, owner=username)
        self.user_subscribe_user_to_context(other, subscribe_context, auth_user=username, expect=201)

    def test_self_subscribe_to_public_context_as_non_manager(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to subscribe myself to a public subscription context
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'

        self.create_user(username)
        self.create_context(create_context, permissions={'subscribe': 'public'})
        self.user_subscribe_user_to_context(username, subscribe_context, expect=201)

    def test_self_subscribe_to_restricted_context_as_non_manager(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to subscribe myself to a restricted subscription context
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'

        self.create_user(username)
        self.create_context(create_context, permissions={'subscribe': 'restricted'})
        self.user_subscribe_user_to_context(username, subscribe_context, expect=403)

    def test_subscribe_user_to_restricted_context_as_non_manager(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to subscribe another user to a restricted subscription context
            I get a Forbidden exception
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'

        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'subscribe': 'restricted'})
        self.user_subscribe_user_to_context(username, subscribe_context, expect=403)

    def test_subscribe_user_to_public_context_as_non_manager(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to subscribe another user to a public subscription context
            I get a Forbidden exception
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'

        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'subscribe': 'public'})
        self.user_subscribe_user_to_context(other, subscribe_context, auth_user=username, expect=403)

    # Unsubscribe tests

    def test_unsubscribe_user_from_context_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to unsubscribe another user from to a context
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'

        self.create_user(username)
        self.create_context(create_context, permissions={'unsubscribe': 'restricted'})
        chash = sha1(subscribe_context['object']['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.admin_unsubscribe_user_from_context(username, chash, expect=204)

    def test_unsubscribe_user_from_context_as_context_owner(self):
        """
            Given i'm a user that doesn't have the Manager role
            And i'm the owner of the context
            When i try to unsubscribe another user from to a context
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'

        self.create_user(username)
        self.create_user(other)

        self.create_context(create_context, permissions={'unsubscribe': 'restricted'}, owner=username)
        chash = sha1(subscribe_context['object']['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.admin_subscribe_user_to_context(other, subscribe_context, expect=201)
        self.user_unsubscribe_user_from_context(other, chash, auth_user=username, expect=204)

    def test_self_unsubscribe_user_from_context_as_non_manager(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to unsubscribe another user from to a context
            I get a Forbidden Exception
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'

        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'unsubscribe': 'restricted'})
        chash = sha1(subscribe_context['object']['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.user_unsubscribe_user_from_context(username, chash, auth_user=other, expect=403)

    def test_unsubscribe_user_from_context_allowed_unsubscribe_as_non_manager(self):
        """
            Given i'm a user that doesn't have the Manager role
            And i have permission to unsubscribe myself
            When i try to unsubscribe myself from the context
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'

        self.create_user(username)
        self.create_context(create_context, permissions={'unsubscribe': 'subscribed'})
        chash = sha1(subscribe_context['object']['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.admin_unsubscribe_user_from_context(username, chash, expect=204)

    def test_unsubscribe_another_user_from_context_allowed_unsubscribe_as_non_manager(self):
        """
            Given i'm a user that doesn't have the Manager role
            And i have permission to unsubscribe myself
            When i try to unsubscribe other person from the context
            I get a Forbidden Exception
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'

        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'unsubscribe': 'subscribed'})
        chash = sha1(subscribe_context['object']['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.admin_subscribe_user_to_context(other, subscribe_context, expect=201)
        self.user_unsubscribe_user_from_context(username, chash, auth_user=other, expect=403)

    # Get context subscriptions

    def test_get_context_subscriptions_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to get all subscriptions from a context
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'

        self.create_user(username)
        self.create_context(create_context, permissions={'unsubscribe': 'restricted'})
        chash = sha1(subscribe_context['object']['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.testapp.get('/contexts/{}/subscriptions'.format(chash), "", headers=oauth2Header(test_manager), status=200)

    def test_get_context_subscriptions_as_owner(self):
        """
            Given i'm a user that doesn't have the Manager role
            And i'm the owner of the context
            When i try to get all subscriptions from a context
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'

        self.create_user(username)
        self.create_user(other)

        self.create_context(create_context, permissions={'unsubscribe': 'restricted'}, owner=username)
        chash = sha1(subscribe_context['object']['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.admin_subscribe_user_to_context(other, subscribe_context, expect=201)
        self.testapp.get('/contexts/{}/subscriptions'.format(chash), "", headers=oauth2Header(username), status=200)

    def test_get_context_subscriptions_as_non_manager_neither_owner(self):
        """
            Given i'm a user that doesn't have the Manager role
            And i'm not the owner of the context
            When i try to get all subscriptions from a context
            I get a Forbidden Exception
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'

        self.create_user(username)
        self.create_user(other)

        self.create_context(create_context, permissions={'unsubscribe': 'restricted'}, owner=username)
        chash = sha1(subscribe_context['object']['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.admin_subscribe_user_to_context(other, subscribe_context, expect=201)
        self.testapp.get('/contexts/{}/subscriptions'.format(chash), "", headers=oauth2Header(other), status=403)

    def test_get_user_subscriptions_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to get all subscriptions from a user
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'

        self.create_user(username)
        self.create_context(create_context, permissions={'unsubscribe': 'restricted'})
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.testapp.get('/people/{}/subscriptions'.format(username), "", headers=oauth2Header(test_manager), status=200)

    def test_get_own_user_subscriptions(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to get all my subscriptions
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'

        self.create_user(username)

        self.create_context(create_context, permissions={'unsubscribe': 'restricted'}, owner=username)
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.testapp.get('/people/{}/subscriptions'.format(username), "", headers=oauth2Header(username), status=200)

    def test_get_user_subscriptions_as_non_manager_neither_own(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to get all subscriptions from another user
            I get a Forbidden Exception
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'

        self.create_user(username)
        self.create_user(other)

        self.create_context(create_context, permissions={'unsubscribe': 'restricted'}, owner=username)
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        self.testapp.get('/people/{}/subscriptions'.format(username), "", headers=oauth2Header(other), status=403)

