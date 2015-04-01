# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header
from max.tests.base import impersonate_payload
from functools import partial
from mock import patch
from paste.deploy import loadapp

import os
import unittest
import json


class TokenACLTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(os.path.dirname(__file__))

        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('messages')
        self.app.registry.max_store.drop_collection('tokens')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)

    # Add new token test

    def test_add_token(self):
        """
            Given i'm a regular user
            When i try to add a device token
            I succeed
        """
        from max.tests.mockers import token

        username = 'sheldon'
        self.create_user(username)

        self.testapp.post('/tokens', json.dumps(token), headers=oauth2Header(username), status=201)

    def test_add_token_impersonated(self):
        """
            Given i'm a Manager user
            When i try to add a device token to someone else
            I succeed
        """
        from max.tests.mockers import token

        username = 'sheldon'
        self.create_user(username)

        self.testapp.post('/tokens', json.dumps(impersonate_payload(token, username)), headers=oauth2Header(test_manager), status=201)

    def test_add_token_impersonated_no_privileges(self):
        """
            Given i'm a regular user
            When i try to add a device token to someone else
            And i'm impersonated as the other user
            I get a Forbidden Exception
        """
        from max.tests.mockers import token

        username = 'sheldon'
        username2 = 'penny'
        self.create_user(username)
        self.create_user(username2)

        self.testapp.post('/tokens', json.dumps(impersonate_payload(token, username)), headers=oauth2Header(username2), status=403)

    # Delete token test

    def test_delete_token(self):
        """
            Given i'm a regular user
            When i try to add delete a device token
            I succeed
        """
        from max.tests.mockers import token

        username = 'sheldon'
        self.create_user(username)

        self.testapp.post('/tokens', json.dumps(token), headers=oauth2Header(username), status=201)
        self.testapp.delete('/tokens/{}'.format(token['token']), '', headers=oauth2Header(username), status=204)

    def test_delete_ohers_token(self):
        """
            Given i'm a regular user
            When i try to delete someone else's device token
            I get a Forbidden Exception
        """
        from max.tests.mockers import token

        username = 'sheldon'
        username2 = 'penny'
        self.create_user(username)
        self.create_user(username2)

        self.testapp.post('/tokens', json.dumps(token), headers=oauth2Header(username), status=201)
        self.testapp.delete('/tokens/{}'.format(token['token']), '', headers=oauth2Header(username2), status=403)

    def test_delete_token_impersonated(self):
        """
            Given i'm a Manager user
            When i try to delete someone else's device token
            I succeed
        """
        from max.tests.mockers import token

        username = 'sheldon'
        self.create_user(username)

        self.testapp.post('/tokens', json.dumps(token), headers=oauth2Header(username), status=201)
        self.testapp.delete('/tokens/{}'.format(token['token']), json.dumps(impersonate_payload({}, test_manager)), headers=oauth2Header(username), status=204)

    def test_delete_token_impersonated_no_privileges(self):
        """
            Given i'm a regular user
            When i try to delete someone else's device token
            And i'm impersonating as the other user
            I get a Forbidden Exception
        """
        from max.tests.mockers import token

        username = 'sheldon'
        username2 = 'penny'
        self.create_user(username)
        self.create_user(username2)

        self.testapp.post('/tokens', json.dumps(token), headers=oauth2Header(username), status=201)
        self.testapp.delete('/tokens/{}'.format(token['token']), json.dumps(impersonate_payload({}, username2)), headers=oauth2Header(username), status=204)

    # Delete all user tokens tests

    def test_delete_user_tokens(self):
        """
            Given i'm a regular user
            When i try to delete all my tokens
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)

        self.testapp.delete('/people/{}/tokens'.format(username), '', headers=oauth2Header(username), status=204)

    def test_delete_user_tokens_impersonated(self):
        """
            Given i'm a Manager user
            When i try to delete another user tokens
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)

        self.testapp.delete('/people/{}/tokens'.format(username), '', headers=oauth2Header(test_manager), status=204)

    def test_delete_user_tokens_impersonated_no_privileges(self):
        """
            Given i'm a regular user
            When i try to delete another user tokens
            I succeed
        """
        username = 'sheldon'
        username2 = 'penny'
        self.create_user(username)
        self.create_user(username2)

        self.testapp.delete('/people/{}/tokens'.format(username), '', headers=oauth2Header(username2), status=403)

    # Delete all user tokens by platform tests

    def test_delete_user_tokens_by_platform(self):
        """
            Given i'm a regular user
            When i try to delete all my tokens by platform
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)

        self.testapp.delete('/people/{}/tokens/platforms/{}'.format(username, 'ios'), '', headers=oauth2Header(username), status=204)

    def test_delete_user_tokens_by_platform_impersonated(self):
        """
            Given i'm a Manager user
            When i try to delete another user tokens by platform
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)

        self.testapp.delete('/people/{}/tokens/platforms/{}'.format(username, 'ios'), '', headers=oauth2Header(test_manager), status=204)

    def test_delete_user_tokens_by_platform_impersonated_no_privileges(self):
        """
            Given i'm a regular user
            When i try to delete another user tokens by platform
            I succeed
        """
        username = 'sheldon'
        username2 = 'penny'
        self.create_user(username)
        self.create_user(username2)

        self.testapp.delete('/people/{}/tokens/platforms/{}'.format(username, 'ios'), '', headers=oauth2Header(username2), status=403)

    # Get conversation user's tokens tests

    def test_get_conversation_tokens_as_manager(self):
        """
            Given i'm a Manager user
            When i try to list all tokens of users of a conversation
            I succeed
        """
        from max.tests.mockers import message

        username = 'messi'
        username2 = 'xavi'
        self.create_user(username)
        self.create_user(username2)
        chash = self.testapp.post('/conversations', json.dumps(message), oauth2Header(username), status=201).json['id']
        self.testapp.get('/conversations/{}/tokens'.format(chash), '', headers=oauth2Header(test_manager), status=200)

    def test_get_conversation_tokens_as_anyone_else(self):
        """
            Given i'm a regular user
            When i try to list all tokens of users of a conversation
            I get a Forbidden Exception
        """
        from max.tests.mockers import message

        username = 'messi'
        username2 = 'xavi'
        self.create_user(username)
        self.create_user(username2)
        chash = self.testapp.post('/conversations', json.dumps(message), oauth2Header(username), status=201).json['id']
        self.testapp.get('/conversations/{}/tokens'.format(chash), '', headers=oauth2Header(username), status=403)

    # Get context user's tokens tests

    def test_get_context_tokens_as_manager(self):
        """
            Given i'm a Manager user
            When i try to list all tokens of users subscribed to a context
            I succeed
        """
        from max.tests.mockers import create_context

        chash = self.create_context(create_context).json['hash']

        self.testapp.get('/contexts/{}/tokens'.format(chash), '', headers=oauth2Header(test_manager), status=200)

    def test_get_context_tokens_as_anyone_else(self):
        """
            Given i'm a regular user
            When i try to list all tokens of users subscribed to a context
            I get a Forbidden Exception
        """
        from max.tests.mockers import create_context

        username = 'sheldon'
        self.create_user(username)
        chash = self.create_context(create_context).json['hash']

        self.testapp.get('/contexts/{}/tokens'.format(chash), '', headers=oauth2Header(username), status=403)
