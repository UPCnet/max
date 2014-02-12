# -*- coding: utf-8 -*-
import os
import json
import unittest
from functools import partial

from paste.deploy import loadapp
from mock import patch

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header, mock_post
from max.tests import test_manager, test_default_security


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests_vip.ini', relative_to=conf_dir)
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

    # BEGIN TESTS
    # !!! IMPORTANT INFO !!! All this tests are run with the max.restricted_user_visibility_mode=True in set the .ini

    def test_add_vip_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('VIP', username), "", oauth2Header(test_manager), status=201)

    def test_get_people_as_vip(self):
        """
            Given i'm a vip user
            When I search users
            Then I can see them all
        """
        usernamenotvip1 = 'user1'
        usernamenotvip2 = 'user2'
        usernamevip = 'uservip'

        self.create_user(usernamenotvip1)
        self.create_user(usernamenotvip2)
        self.create_user(usernamevip)

        self.testapp.post('/admin/security/roles/%s/users/%s' % ('VIP', usernamevip), "", oauth2Header(test_manager), status=201)

        res = self.testapp.get('/people', "", oauth2Header(usernamevip), status=200)

        self.assertEqual(len(res.json), 3)
        self.assertEqual(res.json[0]['username'], usernamevip)
        self.assertEqual(res.json[1]['username'], usernamenotvip2)
        self.assertEqual(res.json[2]['username'], usernamenotvip1)

    def test_get_people_as_non_vip(self):
        """
            Given i'm a non vip user
            When I search users
            Then I can see only the non-vip people on the same contexts as I
        """
        from .mockers import subscribe_context, create_context
        usernamenotvip1 = 'user1'
        usernamenotvip2 = 'user2'
        usernamenotvip3 = 'user3'
        usernamevip = 'uservip'

        self.create_user(usernamenotvip1)
        self.create_user(usernamenotvip2)
        self.create_user(usernamenotvip3)
        self.create_user(usernamevip)

        self.create_context(create_context)
        self.admin_subscribe_user_to_context(usernamenotvip1, subscribe_context)
        self.admin_subscribe_user_to_context(usernamenotvip2, subscribe_context)

        self.testapp.post('/admin/security/roles/%s/users/%s' % ('VIP', usernamevip), "", oauth2Header(test_manager), status=201)

        res = self.testapp.get('/people', "", oauth2Header(usernamenotvip1), status=200)

        self.assertEqual(len(res.json), 2)
        self.assertEqual(res.json[0]['username'], usernamenotvip2)
        self.assertEqual(res.json[1]['username'], usernamenotvip1)

    def test_start_conversation_with_some_people_being_a_vip(self):
        from .mockers import message
        """
            Given i'm a vip user
            When I try to start a conversation with anyone
            Then I can start the conversation
        """
        usernamenotvip = 'user1'
        usernamevip1 = 'uservip1'
        usernamevip2 = 'uservip2'

        self.create_user(usernamenotvip)
        self.create_user(usernamevip1)
        self.create_user(usernamevip2)        

        message = dict(message)
        message['contexts'][0]['participants'] = [usernamevip1, usernamevip2, usernamenotvip]

        self.testapp.post('/admin/security/roles/%s/users/%s' % ('VIP', usernamevip1), "", oauth2Header(test_manager), status=201)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('VIP', usernamevip2), "", oauth2Header(test_manager), status=201)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(usernamevip1), status=201)
        
    def test_start_conversation_with_a_vip_being_not_being_a_vip(self):
        from .mockers import message

        """
            Given i'm not a vip user
            When I try to start a conversation with a vip
            Then I cannot start the conversation
        """
        usernamenotvip = 'user1'
        usernamevip1 = 'uservip1'
        usernamevip2 = 'uservip2'

        self.create_user(usernamenotvip)
        self.create_user(usernamevip1)
        self.create_user(usernamevip2)        

        message = dict(message)
        message['contexts'][0]['participants'] = [usernamenotvip, usernamevip1]

        self.testapp.post('/admin/security/roles/%s/users/%s' % ('VIP', usernamevip1), "", oauth2Header(test_manager), status=201)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(usernamenotvip), status=401)        

    def test_start_conversation_with_a_non_vip_not_sharing_contexts(self):
        from .mockers import message
        """
            Given i'm not a vip user
            When I try to start a conversation with a non vip
            And I don't share any subscription with the other user
            Then I cannot start the conversation
        """
        usernamenotvip1 = 'user1'
        usernamenotvip2 = 'user2'

        self.create_user(usernamenotvip1)
        self.create_user(usernamenotvip2)

        message = dict(message)
        message['contexts'][0]['participants'] = [usernamenotvip1, usernamenotvip2]

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(usernamenotvip1), status=401)                

    def test_start_conversation_with_a_non_vip_sharing_contexts(self):
        from .mockers import message
        from .mockers import subscribe_context, create_context
        """
            Given i'm not a vip user
            When I try to start a conversation with a non vip
            And I share a subscription with the other user
            Then I can start the conversation
        """
        usernamenotvip1 = 'user1'
        usernamenotvip2 = 'user2'

        self.create_user(usernamenotvip1)
        self.create_user(usernamenotvip2)

        self.create_context(create_context)
        self.admin_subscribe_user_to_context(usernamenotvip1, subscribe_context)
        self.admin_subscribe_user_to_context(usernamenotvip2, subscribe_context)

        message = dict(message)
        message['contexts'][0]['participants'] = [usernamenotvip1, usernamenotvip2]

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(usernamenotvip1), status=201)                        