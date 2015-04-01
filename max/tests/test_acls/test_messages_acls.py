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
import shutil


class MessagesACLTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        self.conf_dir = os.path.dirname(os.path.dirname(__file__))
        self.repository = os.path.join(self.conf_dir, 'repository')
        self.app = loadapp('config:tests.ini', relative_to=self.conf_dir)
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

    def tearDown(self):
        shutil.rmtree(self.repository, ignore_errors=True)

    def test_add_message_to_conversation(self):
        """
            Given i'm a regular user
            And I'm a participant in the conversation
            When i try to add a message to a conversation
            Then i succeed
        """
        from max.tests.mockers import group_message as creation_message
        from max.tests.mockers import message2

        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/conversations/{}/messages'.format(conversation_id), json.dumps(message2), oauth2Header(recipient2), status=201)

    def test_add_message_to_conversation_not_participant(self):
        """
            Given i'm a regular user
            And i'm not a participant in the conversation
            When i try to add a message to a conversation
            Then i get a Forbidden Exception
        """
        from max.tests.mockers import message
        from max.tests.mockers import message2

        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/conversations/{}/messages'.format(conversation_id), json.dumps(message2), oauth2Header(recipient2), status=403)

    def test_add_message_to_conversation_impersonating(self):
        """
            Given i'm a regular user
            When i try to add a message to a conversation
            And i'm impersonating as another user
            Then i get a Forbidden Exception
        """
        from max.tests.mockers import group_message as creation_message
        from max.tests.mockers import message4

        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/conversations/{}/messages'.format(conversation_id), json.dumps(message4), oauth2Header(recipient2), status=403)

    def test_add_message_to_conversation_as_owner_impersonating(self):
        """
            Given i'm a regular user
            And i'm the owner of a conversation
            When i try to add a message to a conversation
            And i'm impersonating as another user
            Then i get a Forbidden Exception
        """
        from max.tests.mockers import message
        from max.tests.mockers import message4

        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/conversations/{}/messages'.format(conversation_id), json.dumps(message4), oauth2Header(sender), status=403)

    def test_add_message_to_conversation_as_manager_impersonating(self):
        """
            Given i'm a Manager
            When i try to add a message to a conversation
            And i'm impersonating as another user
            Then i succeed
        """
        from max.tests.mockers import message
        from max.tests.mockers import message4

        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/conversations/{}/messages'.format(conversation_id), json.dumps(message4), oauth2Header(test_manager), status=201)

    # Get conversation messages list tests

    def test_get_messages_as_manager(self):
        """
            Given i'm a Manager
            When i try to list a conversation's messages
            Then i succeed
        """
        from max.tests.mockers import message
        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = res.json['contexts'][0]['id']

        self.testapp.get('/conversations/{}/messages'.format(cid), '', oauth2Header(test_manager), status=200)

    def test_get_messages_as_participant(self):
        """
            Given i'm a regular user
            And i'm a conversation participant
            When i try to list a conversation's messages
            Then i succeed
        """
        from max.tests.mockers import message
        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = res.json['contexts'][0]['id']

        self.testapp.get('/conversations/{}/messages'.format(cid), '', oauth2Header(recipient), status=200)

    def test_get_messages_as_non_participant(self):
        """
            Given i'm a regular user
            And i'm not a conversation participant
            When i try to list a conversation's messages
            Then i get a Forbidden Exception
        """
        from max.tests.mockers import message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = res.json['contexts'][0]['id']

        self.testapp.get('/conversations/{}/messages'.format(cid), '', oauth2Header(recipient2), status=403)

    # Get message attachment tests

    def test_get_message_image_as_manager(self):
        """
            Given i'm a Manager
            When i try to view a message image attachment
            Then i succeed
        """
        from max.tests.mockers import message
        from max.tests.mockers import message_with_image
        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = res.json['contexts'][0]['id']

        thefile = open(os.path.join(self.conf_dir, "avatar.png"), "rb")
        files = [('file', 'avatar.png', thefile.read(), 'image/png')]

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        message_id = self.testapp.post('/conversations/%s/messages' % cid, dict(json_data=json.dumps(message_with_image)), oauth2Header(sender), upload_files=files, status=201).json['id']
        self.testapp.get('/messages/%s/image' % (message_id), headers=oauth2Header(test_manager), status=200)

    def test_get_message_image_as_participant(self):
        """
            Given i'm a regular user
            And i'm a conversation participant
            When i try to view a message image attachment
            Then i succeed
        """
        from max.tests.mockers import message
        from max.tests.mockers import message_with_image
        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = res.json['contexts'][0]['id']

        thefile = open(os.path.join(self.conf_dir, "avatar.png"), "rb")
        files = [('file', 'avatar.png', thefile.read(), 'image/png')]

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        message_id = self.testapp.post('/conversations/%s/messages' % cid, dict(json_data=json.dumps(message_with_image)), oauth2Header(sender), upload_files=files, status=201).json['id']
        self.testapp.get('/messages/%s/image' % (message_id), headers=oauth2Header(recipient), status=200)

    def test_get_message_image_as_non_participant(self):
        """
            Given i'm a regular user
            And i'm not a conversation participant
            When i try to view a message image attachment
            Then i get a Forbidden Exception
        """
        from max.tests.mockers import message
        from max.tests.mockers import message_with_image
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = res.json['contexts'][0]['id']

        thefile = open(os.path.join(self.conf_dir, "avatar.png"), "rb")
        files = [('file', 'avatar.png', thefile.read(), 'image/png')]

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        message_id = self.testapp.post('/conversations/%s/messages' % cid, dict(json_data=json.dumps(message_with_image)), oauth2Header(sender), upload_files=files, status=201).json['id']
        self.testapp.get('/messages/%s/image' % (message_id), headers=oauth2Header(recipient2), status=403)

    def test_get_message_file_as_manager(self):
        """
            Given i'm a Manager
            When i try to view a file attachment
            Then i succeed
        """
        from max.tests.mockers import message
        from max.tests.mockers import message_with_file
        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = res.json['contexts'][0]['id']

        thefile = open(os.path.join(self.conf_dir, "map.pdf"), "rb")
        files = [('file', 'map.pdf', thefile.read(), 'application/pdf')]

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        message_id = self.testapp.post('/conversations/%s/messages' % cid, dict(json_data=json.dumps(message_with_file)), oauth2Header(sender), upload_files=files, status=201).json['id']
        self.testapp.get('/messages/%s/file/download' % (message_id), headers=oauth2Header(test_manager), status=200)

    def test_get_message_file_as_participant(self):
        """
            Given i'm a regular user
            And i'm a conversation participant
            When i try to view a file attachment
            Then i succeed
        """
        from max.tests.mockers import message
        from max.tests.mockers import message_with_file
        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = res.json['contexts'][0]['id']

        thefile = open(os.path.join(self.conf_dir, "map.pdf"), "rb")
        files = [('file', 'map.pdf', thefile.read(), 'application/pdf')]

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        message_id = self.testapp.post('/conversations/%s/messages' % cid, dict(json_data=json.dumps(message_with_file)), oauth2Header(sender), upload_files=files, status=201).json['id']
        self.testapp.get('/messages/%s/file/download' % (message_id), headers=oauth2Header(recipient), status=200)

    def test_get_message_file_as_non_participant(self):
        """
            Given i'm nota regular user
            And i'm not a conversation participant
            When i try to view a file attachment
            Then i get a Forbidden Exception
        """
        from max.tests.mockers import message
        from max.tests.mockers import message_with_file
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = res.json['contexts'][0]['id']

        thefile = open(os.path.join(self.conf_dir, "map.pdf"), "rb")
        files = [('file', 'map.pdf', thefile.read(), 'application/pdf')]

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        message_id = self.testapp.post('/conversations/%s/messages' % cid, dict(json_data=json.dumps(message_with_file)), oauth2Header(sender), upload_files=files, status=201).json['id']
        self.testapp.get('/messages/%s/file/download' % (message_id), headers=oauth2Header(recipient2), status=403)

