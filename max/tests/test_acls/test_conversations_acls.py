# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager, test_manager2
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


class ConversationsACLTests(unittest.TestCase, MaxTestBase):

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

    # Add conversations tests

    def test_create_new_conversation(self):
        """
            Given i'm a regular user
            When I try to create a new conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)

    def test_create_new_conversation_without_oneself(self):
        """
            Given i'm a regular user
            When I try to create a new conversation
            And i'm not in the participants list
            Then I get a Forbidden Exception
        """
        from .mockers import message_oneself
        sender = 'xavi'
        self.create_user(sender)

        self.testapp.post('/conversations', json.dumps(message_oneself), oauth2Header(sender), status=403)

    def test_create_new_conversation_as_manager(self):
        """
            Given i'm a Manager
            When I try to create a new conversation
            And i'm not in the participants list
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(test_manager), status=201)

    # View conversation tests

    def test_view_conversation_as_manager(self):
        """
            Given i'm a Manager
            When I try to view an existing conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.get('/conversations/{}'.format(cid), '', oauth2Header(test_manager), status=200)

    def test_view_conversation_as_owner(self):
        """
            Given i'm a regular user
            And i'm the owner of the conversation
            When I try to view an existing conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.get('/conversations/{}'.format(cid), '', oauth2Header(sender), status=200)

    def test_view_conversation_as_participant(self):
        """
            Given i'm a regular user
            And i'm a regular conversation participant
            When I try to view an existing conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.get('/conversations/{}'.format(cid), '', oauth2Header(recipient), status=200)

    def test_view_conversation_as_anyone_else(self):
        """
            Given i'm a regular user
            And i'm not in the conversation
            When I try to view an existing conversation
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.get('/conversations/{}'.format(cid), '', oauth2Header(recipient2), status=403)

    # View conversation subscription tests

    def test_view_conversation_subscription_as_manager(self):
        """
            Given i'm a Manager
            When I try to view an existing conversation subscription
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.get('/people/{}/conversations/{}'.format(sender, cid), '', oauth2Header(test_manager), status=200)

    def test_view_conversation_subscription_as_owner(self):
        """
            Given i'm a regular user
            And i'm the owner of the conversation
            When I try to view an existing conversation subscription
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.get('/people/{}/conversations/{}'.format(sender, cid), '', oauth2Header(sender), status=200)

    def test_view_conversation_subscription_as_participant(self):
        """
            Given i'm a regular user
            And i'm a regular conversation participant
            When I try to view my conversation subscription
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.get('/people/{}/conversations/{}'.format(recipient, cid), '', oauth2Header(recipient), status=200)

    def test_view_conversation_subscription_as_other_participant(self):
        """
            Given i'm a regular user
            And i'm a regular conversation participant
            When I try to view other's conversation subscription
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.get('/people/{}/conversations/{}'.format(sender, cid), '', oauth2Header(recipient), status=403)

    def test_view_conversation_subscription_as_anyone_else(self):
        """
            Given i'm a regular user
            And i'm not in the conversation
            When I try to view an existing conversation subscription
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.get('/people/{}/conversations/{}'.format(recipient, cid), '', oauth2Header(recipient2), status=403)

    # Get all conversations tests

    def test_list_all_conversations(self):
        """
            Given i'm a regular user
            And i'm a regular conversation participant
            When I try to list all conversations
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)

        self.testapp.get('/people/{}/conversations'.format(sender), '', oauth2Header(sender), status=200)

    # Modify conversation tests

    def test_modify_conversation_as_manager(self):
        """
            Given i'm a Manager
            When I try to modify a conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.put('/conversations/{}'.format(cid), '{"displayName": "Nou nom"}', oauth2Header(test_manager), status=200)

    def test_modify_conversation_as_owner(self):
        """
            Given i'm a regular user
            And i'm the owner of the conversation
            When I try to modify a conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.put('/conversations/{}'.format(cid), '{"displayName": "Nou nom"}', oauth2Header(sender), status=200)

    def test_modify_conversation_as_participant(self):
        """
            Given i'm a regular user
            And i'm a regular conversation participant
            When I try to modify a conversation
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.put('/conversations/{}'.format(cid), '{"displayName": "Nou nom"}', oauth2Header(recipient), status=403)

    def test_modify_conversation_as_anyone_else(self):
        """
            Given i'm a regular user
            And i'm not in the conversation
            When I try to modify a conversation
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.put('/conversations/{}'.format(cid), '{"displayName": "Nou nom"}', oauth2Header(recipient2), status=403)

    # Delete conversation tests

    def test_delete_conversation_as_manager(self):
        """
            Given i'm a Manager
            When I try to delete a conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.delete('/conversations/{}'.format(cid), '', oauth2Header(test_manager), status=204)

    def test_delete_conversation_as_owner(self):
        """
            Given i'm a regular user
            And i'm the owner of the conversation
            When I try to delete a conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.delete('/conversations/{}'.format(cid), '', oauth2Header(sender), status=204)

    def test_delete_conversation_as_participant(self):
        """
            Given i'm a regular user
            And i'm a regular conversation participant
            When I try to delete a conversation
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.delete('/conversations/{}'.format(cid), '', oauth2Header(recipient), status=403)

    def test_delete_conversation_as_anyone_else(self):
        """
            Given i'm a regular user
            And i'm not in the conversation
            When I try to delete a conversation
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.delete('/conversations/{}'.format(cid), '', oauth2Header(recipient2), status=403)

    # Purge conversations tests

    def test_delete_all_conversations_as_manager(self):
        """
            Given i'm a Manager
            When I try to purge all existing conversations
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)

        self.testapp.delete('/conversations', '', oauth2Header(test_manager), status=204)

    def test_delete_all_conversations_as_anyone_else(self):
        """
            Given i'm a regular user
            When I try to purge all existing conversations
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)

        self.testapp.delete('/conversations', '', oauth2Header(sender), status=403)

    # Add participant to conversation tests

    def test_add_participant_as_manager(self):
        """
            Given i'm a Manager
            When I try to add a new participant to an existing conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.post('/people/{}/conversations/{}'.format(recipient2, cid), '', oauth2Header(test_manager), status=201)

    def test_add_participant_as_owner(self):
        """
            Given i'm a regular user
            And i'm the owner of the conversation
            When I try to add a new participant to an existing conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.post('/people/{}/conversations/{}'.format(recipient2, cid), '', oauth2Header(sender), status=201)

    def test_add_participant_as_participant(self):
        """
            Given i'm a regular user
            And i'm a regular conversation participant
            When I try to add a new participant to an existing conversation
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.post('/people/{}/conversations/{}'.format(recipient2, cid), '', oauth2Header(recipient), status=403)

    def test_auto_join(self):
        """
            Given i'm a regular user
            When I try to add myself as a new participant to an existing conversation
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.post('/people/{}/conversations/{}'.format(recipient2, cid), '', oauth2Header(recipient2), status=403)

    # Delete participant to conversation tests

    def test_delete_participant_as_manager(self):
        """
            Given i'm a Manager
            When I try to delete a new participant from an existing conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient, cid), '', oauth2Header(test_manager), status=204)

    def test_delete_participant_as_owner(self):
        """
            Given i'm a regular user
            And i'm the owner of the conversation
            When I try to delete a new participant from an existing conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient2, cid), '', oauth2Header(sender), status=204)

    def test_delete_participant_as_participant(self):
        """
            Given i'm a regular user
            And i'm a regular conversation participant
            When I try to delete a participant from an existing conversation
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.delete('/people/{}/conversations/{}'.format(sender, cid), '', oauth2Header(recipient), status=403)

    def test_leave_as_owner(self):
        """
            Given i'm the owner of the conversation
            When I try to leave an existing conversation
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.delete('/people/{}/conversations/{}'.format(sender, cid), '', oauth2Header(sender), status=403)

    def test_leave(self):
        """
            Given i'm a regular user
            When I try to leave an existing conversation
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient, cid), '', oauth2Header(recipient), status=204)

    # Transfer ownership tests

    def test_transfer_ownership_as_manager(self):
        """
            Given i'm a Manager
            When I try to transfer a conversation to another user
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.put('/conversations/{}/owner'.format(cid), json.dumps({'actor': {'username': recipient}}), oauth2Header(test_manager), status=200)

    def test_transfer_ownership_as_owner(self):
        """
            Given i'm a regular user
            And i'm the owner of the conversation
            When I try to transfer a conversation to another user
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.put('/conversations/{}/owner'.format(cid), json.dumps({'actor': {'username': recipient}}), oauth2Header(sender), status=200)

    def test_transfer_ownership_as_participant(self):
        """
            Given i'm a regular user
            And i'm the owner of the conversation
            When I try to transfer a conversation to another user
            Then I succeed
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.put('/conversations/{}/owner'.format(cid), json.dumps({'actor': {'username': recipient}}), oauth2Header(recipient), status=403)

    def test_transfer_ownership_as_anyone_else(self):
        """
            Given i'm a regular user
            And i'm not in the conversation
            When I try to transfer a conversation to another user
            Then I get a Forbidden Exception
        """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.get('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.put('/conversations/{}/owner'.format(cid), json.dumps({'actor': {'username': recipient}}), oauth2Header(recipient2), status=403)
