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

    def test_post_message_to_conversation_does_not_exists_yet(self):
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        result = json.loads(res.text)

        self.assertEqual(result.get("contexts", None)[0].get("object", None).get("participants", None), sorted([sender, recipient]))
        self.assertEqual(result.get("contexts", None)[0].get("object", None).get("objectType", None), "conversation")
        self.assertEqual(result.get("object", None).get("objectType", None), "message")

    def test_post_message_to_conversation_check_conversation(self):
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)

        conversation = self.app.registry.max_store.contexts.find_one()
        permissions = {'read': 'subscribed', 'write': 'subscribed', 'join': 'restricted', 'invite': 'restricted'}
        participants = list([sender, recipient])
        participants.sort()
        alltogether = ''.join(participants)
        chash = sha1(alltogether).hexdigest()

        self.assertEqual(conversation.get("object", None).get("participants", None), sorted([sender, recipient]))
        self.assertEqual(conversation.get("object", None).get("objectType", None), "conversation")
        self.assertEqual(conversation.get("permissions", None), permissions)
        self.assertEqual(conversation.get("hash", None), chash)

    def test_post_messages_to_an_already_existing_conversation_check_not_duplicated_conversation(self):
        from .mockers import message, message2
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        self.testapp.post('/conversations', json.dumps(message2), oauth2Header(sender), status=201)

        res = self.testapp.get('/conversations', {}, oauth2Header(sender), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get("totalItems", None), 1)

    def test_post_messages_to_an_already_existing_conversation(self):
        from .mockers import message, message2
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        self.testapp.post('/conversations', json.dumps(message2), oauth2Header(sender), status=201)

        participants = list([sender, recipient])
        participants.sort()
        alltogether = ''.join(participants)
        chash = sha1(alltogether).hexdigest()

        res = self.testapp.get('/conversations/%s/messages' % chash, "", oauth2Header(sender), status=200)
        result = json.loads(res.text)

        self.assertEqual(result.get("totalItems", None), 2)
        self.assertEqual(result.get("items")[0].get("contexts", None)[0].get("hash", None), chash)
        self.assertEqual(result.get("items")[0].get("contexts", None)[0].get("object", None).get("participants", None), sorted([sender, recipient]))
        self.assertEqual(result.get("items")[0].get("contexts", None)[0].get("object", None).get("objectType", None), "conversation")
        self.assertEqual(result.get("items")[0].get("object", None).get("objectType", None), "message")

    def test_post_messages_to_a_known_conversation_without_specifying_participants(self):
        from .mockers import message, message3
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        participants = list([sender, recipient])
        participants.sort()
        alltogether = ''.join(participants)
        chash = sha1(alltogether).hexdigest()

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        self.testapp.post('/conversations/%s/messages' % chash, json.dumps(message3), oauth2Header(sender), status=201)

        res = self.testapp.get('/conversations/%s/messages' % chash, "", oauth2Header(sender), status=200)
        result = json.loads(res.text)

        self.assertEqual(result.get("totalItems", None), 2)
        self.assertEqual(result.get("items")[0].get("contexts", None)[0].get("hash", None), chash)
        self.assertEqual(result.get("items")[0].get("contexts", None)[0].get("object", None).get("participants", None), sorted([sender, recipient]))
        self.assertEqual(result.get("items")[0].get("contexts", None)[0].get("object", None).get("objectType", None), "conversation")
        self.assertEqual(result.get("items")[0].get("object", None).get("objectType", None), "message")

    def test_get_messages_from_a_conversation_as_a_recipient(self):
        from .mockers import message, message2
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        self.testapp.post('/conversations', json.dumps(message2), oauth2Header(sender), status=201)

        participants = list([sender, recipient])
        participants.sort()
        alltogether = ''.join(participants)
        chash = sha1(alltogether).hexdigest()

        res = self.testapp.get('/conversations/%s/messages' % chash, "", oauth2Header(recipient), status=200)
        result = json.loads(res.text)

        self.assertEqual(result.get("totalItems", None), 2)

    def test_get_messages_from_a_conversation_for_user_not_in_participants(self):
        from .mockers import message, message2
        sender = 'messi'
        recipient = 'xavi'
        external = 'casillas'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(external)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        self.testapp.post('/conversations', json.dumps(message2), oauth2Header(sender), status=201)

        participants = list([sender, recipient])
        participants.sort()
        alltogether = ''.join(participants)
        chash = sha1(alltogether).hexdigest()

        self.testapp.get('/conversations/%s/messages' % chash, "", oauth2Header(external), status=400)

    def test_get_conversations_for_an_user(self):
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        result = json.loads(res.text)

        self.assertEqual(result.get("contexts", None)[0].get("object", None).get("participants", None), sorted([sender, recipient]))
        self.assertEqual(result.get("contexts", None)[0].get("object", None).get("objectType", None), "conversation")
        self.assertEqual(result.get("object", None).get("objectType", None), "message")

        res = self.testapp.get('/conversations', "", oauth2Header(sender), status=200)
        result = json.loads(res.text)

        self.assertEqual(result.get("totalItems", None), 1)
        self.assertEqual(result.get("items")[0].get("object", "").get("objectType", ""), "conversation")
