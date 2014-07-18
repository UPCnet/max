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

    def tearDown(self):
        import pyramid.testing
        pyramid.testing.tearDown()

    def test_add_nonvisible_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('NonVisible', username), "", oauth2Header(test_manager), status=201)

    # ############################################################################################################################
    #
    #  !!! IMPORTANT INFO !!! All this tests are run with the max.restricted_user_visibility_mode=False in set the .ini
    #  Tests for NonVisible users WITH restricted_user_visibility live in test_restricted_user_visibility.py, wich uses a different .ini
    #
    #  The tests on this file are the same tests on test_restricted_user_visibility.py but WITHOUT excluding the ones that test
    #  Users with shared contexts, And with different asserst, as here we have the restricted_user_visibility disabled, and shared subscriptions doesn't affect us
    #
    ##############################################################################################################################

    # Tests for listing people without sharing contexts (2 tests)

    def test_get_people_as_a_nonvisible_user_without_subscriptions(self):
        """
            Given i'm a nonvisible user
            When I search users
            Then I see everyone
        """
        username_visible1 = 'user1'
        username_visible2 = 'user2'
        username_nonvisible1 = 'usernonvisible1'
        username_nonvisible2 = 'usernonvisible2'

        self.create_user(username_visible1)
        self.create_user(username_visible2)
        self.create_user(username_nonvisible1)
        self.create_user(username_nonvisible2)

        self.testapp.post('/admin/security/roles/%s/users/%s' % ('NonVisible', username_nonvisible1), "", oauth2Header(test_manager), status=201)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('NonVisible', username_nonvisible2), "", oauth2Header(test_manager), status=201)

        res = self.testapp.get('/people', "", oauth2Header(username_nonvisible1), status=200)

        self.assertEqual(len(res.json), 4)
        self.assertEqual(res.json[0]['username'], username_nonvisible2)
        self.assertEqual(res.json[1]['username'], username_nonvisible1)
        self.assertEqual(res.json[2]['username'], username_visible2)
        self.assertEqual(res.json[3]['username'], username_visible1)

    def test_get_people_as_visible_user_without_subscriptions(self):
        """
            Given i'm a visible user
            When I search users
            Then I only see the visible ones
        """
        username_visible1 = 'user1'
        username_visible2 = 'user2'
        username_nonvisible1 = 'usernonvisible1'
        username_nonvisible2 = 'usernonvisible2'

        self.create_user(username_visible1)
        self.create_user(username_visible2)
        self.create_user(username_nonvisible1)
        self.create_user(username_nonvisible2)

        self.testapp.post('/admin/security/roles/%s/users/%s' % ('NonVisible', username_nonvisible1), "", oauth2Header(test_manager), status=201)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('NonVisible', username_nonvisible2), "", oauth2Header(test_manager), status=201)

        res = self.testapp.get('/people', "", oauth2Header(username_visible1), status=200)

        self.assertEqual(len(res.json), 2)
        self.assertEqual(res.json[0]['username'], username_visible2)
        self.assertEqual(res.json[1]['username'], username_visible1)

    # Tests for start Conversations without sharing contexts (4 tests)

    def test_start_conversation_with_visible_as_nonvisible_without_sharing_contexts(self):
        from .mockers import message
        """
            Given i'm a nonvisible person
            When I try to start a conversation with a visible
            Then I can start the conversation
        """
        username_visible1 = 'user1'
        username_nonvisible1 = 'usernonvisible1'

        self.create_user(username_visible1)
        self.create_user(username_nonvisible1)

        message = deepcopy(message)
        message['contexts'][0]['participants'] = [username_nonvisible1, username_visible1]

        self.testapp.post('/admin/security/roles/%s/users/%s' % ('NonVisible', username_nonvisible1), "", oauth2Header(test_manager), status=201)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(username_nonvisible1), status=201)

    def test_start_conversation_with_nonvisible_as_nonvisible_without_sharing_contexts(self):
        from .mockers import message
        """
            Given i'm a nonvisible person
            When I try to start a conversation with a nonvisible
            Then I can start the conversation
        """
        username_nonvisible1 = 'usernonvisible1'
        username_nonvisible2 = 'usernonvisible2'

        self.create_user(username_nonvisible1)
        self.create_user(username_nonvisible2)

        message = deepcopy(message)
        message['contexts'][0]['participants'] = [username_nonvisible1, username_nonvisible2]

        self.testapp.post('/admin/security/roles/%s/users/%s' % ('NonVisible', username_nonvisible1), "", oauth2Header(test_manager), status=201)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('NonVisible', username_nonvisible2), "", oauth2Header(test_manager), status=201)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(username_nonvisible1), status=201)

    # In fact, this test is really a duplicate of some test in test_conversations, as
    # all users implied in conversation are regular users. Leaving it here for coherence
    def test_start_conversation_with_visible_as_visible_without_sharing_contexts(self):
        from .mockers import message
        """
            Given i'm a visible person
            When I try to start a conversation with a visible
            Then I can start the conversation
        """
        username_visible1 = 'user1'
        username_visible2 = 'user2'

        self.create_user(username_visible1)
        self.create_user(username_visible2)

        message = deepcopy(message)
        message['contexts'][0]['participants'] = [username_visible2, username_visible1]

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(username_visible1), status=201)

    def test_start_conversation_with_nonvisible_as_visible_without_sharing_contexts(self):
        from .mockers import message
        """
            Given i'm a visible person
            When I try to start a conversation with a nonvisible
            Then I cannot start the conversation
        """
        username_visible1 = 'user1'
        username_nonvisible1 = 'usernonvisible1'

        self.create_user(username_visible1)
        self.create_user(username_nonvisible1)

        message = deepcopy(message)
        message['contexts'][0]['participants'] = [username_nonvisible1, username_visible1]

        self.testapp.post('/admin/security/roles/%s/users/%s' % ('NonVisible', username_nonvisible1), "", oauth2Header(test_manager), status=201)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(username_visible1), status=401)

