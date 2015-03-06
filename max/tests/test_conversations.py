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
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('messages')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

    # BEGIN TESTS

    def test_post_message_to_conversation_does_not_exists_yet(self):
        """ doctest .. http:post:: /conversations """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)

        self.assertEqual(res.json["contexts"][0]["objectType"], "conversation")
        self.assertEqual(res.json["objectType"], "message")
        self.assertEqual(res.json["object"]["objectType"], "note")

    def test_post_message_to_conversation_to_oneself(self):
        """ doctest .. http:post:: /conversations """
        from .mockers import message_oneself
        sender = 'messi'
        self.create_user(sender)

        self.testapp.post('/conversations', json.dumps(message_oneself), oauth2Header(sender), status=400)
        res = self.testapp.get('/conversations', '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json), 0)

    def test_post_message_to_conversation_to_only_oneself(self):
        """ doctest .. http:post:: /conversations """
        from .mockers import message_oneself_only
        sender = 'messi'
        self.create_user(sender)

        self.testapp.post('/conversations', json.dumps(message_oneself_only), oauth2Header(sender), status=400)
        res = self.testapp.get('/conversations', '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json), 0)

    def test_post_message_to_conversation_without_context(self):
        """
        """
        from .mockers import invalid_message_no_context
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(invalid_message_no_context), oauth2Header(sender), status=400)

    def test_post_message_to_conversation_without_participants(self):
        """
        """
        from .mockers import invalid_message_no_participants
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(invalid_message_no_participants), oauth2Header(sender), status=400)

    def test_post_message_to_conversation_without_sender_in_participants(self):
        """
        """
        from .mockers import invalid_message_without_sender
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(invalid_message_without_sender), oauth2Header(sender), status=400)

    def test_post_message_to_conversation_does_not_exists_yet_with_wrong_message_type(self):
        """ doctest .. http:post:: /conversations
            TO check that a failed 2-people conversation creation succeds after a failed first attempt
        """
        from .mockers import wrong_message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(wrong_message), oauth2Header(sender), status=400)
        res = self.testapp.get('/conversations', '', oauth2Header(sender), status=200)

        self.assertEqual(len(res.json), 0)

    def test_post_message_to_conversation_check_conversation(self):
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        resp = self.testapp.get('/conversations/{}'.format(cid), '', oauth2Header(sender), status=200)
        permissions = {'read': 'subscribed', 'write': 'subscribed', 'subscribe': 'restricted', 'unsubscribe': 'public', 'invite': 'restricted'}
        self.assertEqual(resp.json.get("participants", None)[0]['username'], sender)
        self.assertEqual(resp.json.get("participants", None)[1]['username'], recipient)
        self.assertEqual(resp.json.get("objectType", None), "conversation")
        self.assertEqual(resp.json.get("tags", None), [])
        self.assertEqual(resp.json.get("permissions", None), permissions)
        self.assertEqual(str(resp.json.get("id", '')), cid)
        return cid, sender

    def test_get_user_conversation_subscription(self):
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        resp = self.testapp.get('/people/{}/conversations/{}'.format(sender, cid), '', oauth2Header(sender), status=200)
        self.assertEqual(resp.json.get("participants", None)[0]['username'], sender)
        self.assertEqual(resp.json.get("participants", None)[1]['username'], recipient)
        self.assertEqual(resp.json.get("objectType", None), "conversation")
        self.assertEqual(resp.json.get("tags", None), [])
        self.assertIn('lastMessage', resp.json)

        permissions = ['read', 'write', 'unsubscribe']
        self.assertEqual(resp.json.get("permissions", None), permissions)

    def test_last_message_in_user_info(self):
        from .mockers import message, message2, message3
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        self.testapp.post('/conversations/%s/messages' % cid, json.dumps(message2), oauth2Header(sender), status=201)
        self.testapp.post('/conversations/%s/messages' % cid, json.dumps(message3), oauth2Header(sender), status=201)

        resp = self.testapp.get('/people/{}'.format(sender), '', oauth2Header(sender), status=200)

        self.assertEqual(resp.json['talkingIn'][0]['lastMessage']['content'], message3['object']['content'])

    def test_post_messages_to_an_already_existing_two_people_conversation_check_not_duplicated_conversation(self):
        from .mockers import message, message2
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)
        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        res = self.testapp.post('/conversations', json.dumps(message2), oauth2Header(sender), status=201)
        cid2 = str(res.json['contexts'][0]['id'])

        self.assertEqual(cid, cid2)

        res = self.testapp.get('/conversations/%s/messages' % cid, {}, oauth2Header(sender), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 2)

    def test_post_message_to_new_conversation_check_message_not_in_another_conversation(self):
        from .mockers import message, message_s
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid1 = str(res.json['contexts'][0]['id'])
        res = self.testapp.post('/conversations', json.dumps(message_s), oauth2Header(sender), status=201)
        cid2 = str(res.json['contexts'][0]['id'])

        self.assertNotEqual(cid1, cid2)

        res = self.testapp.get('/conversations/%s/messages' % cid1, {}, oauth2Header(sender), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)

    def test_post_messages_to_an_already_existing_conversation(self):
        from .mockers import message, message2
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        self.testapp.post('/conversations/%s/messages' % cid, json.dumps(message2), oauth2Header(sender), status=201)

        res = self.testapp.get('/conversations/%s/messages' % cid, "", oauth2Header(sender), status=200)
        result = json.loads(res.text)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].get("contexts", None)[0].get("id", None), cid)
        self.assertEqual(result[0].get("contexts", None)[0].get("objectType", None), "conversation")
        self.assertEqual(result[0].get("objectType", None), "message")

    def test_post_messages_to_a_known_conversation_without_specifying_participants(self):
        from .mockers import message, message3
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        self.testapp.post('/conversations/%s/messages' % cid, json.dumps(message3), oauth2Header(sender), status=201)

        res = self.testapp.get('/conversations/%s/messages' % cid, "", oauth2Header(sender), status=200)
        result = json.loads(res.text)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].get("contexts", None)[0].get("id", None), cid)
        self.assertEqual(result[0].get("contexts", None)[0].get("objectType", None), "conversation")
        self.assertEqual(result[0].get("objectType", None), "message")

    def test_get_messages_from_a_conversation_as_a_recipient(self):
        """ doctest .. http:get:: /conversations/{id}/messages """
        from .mockers import message, message2
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)
        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        self.testapp.post('/conversations/%s/messages' % cid, json.dumps(message2), oauth2Header(sender), status=201)

        res = self.testapp.get('/conversations/%s/messages' % cid, "", oauth2Header(recipient), status=200)
        result = json.loads(res.text)

        self.assertEqual(len(result), 2)

    def test_get_conversation_for_user_not_in_participants(self):
        from .mockers import message, message2
        sender = 'messi'
        recipient = 'xavi'
        external = 'casillas'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(external)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        self.testapp.post('/conversations/%s/messages' % cid, json.dumps(message2), oauth2Header(sender), status=201)
        self.testapp.get('/conversations/%s' % cid, "", oauth2Header(external), status=401)

    def test_get_messages_from_a_conversation_for_user_not_in_participants(self):
        from .mockers import message, message2
        sender = 'messi'
        recipient = 'xavi'
        external = 'casillas'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(external)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        self.testapp.post('/conversations/%s/messages' % cid, json.dumps(message2), oauth2Header(sender), status=201)

        res = self.testapp.get('/conversations/%s/messages' % cid, "", oauth2Header(external), status=401)

    def test_get_conversations_for_an_user(self):
        """ doctest .. http:get:: /conversations """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        result = json.loads(res.text)

        self.assertEqual(result.get("contexts", None)[0].get("objectType", None), "conversation")
        self.assertEqual(result.get("objectType", None), "message")
        self.assertEqual(result.get("object", None).get("objectType", None), "note")

        res = self.testapp.get('/conversations', "", oauth2Header(sender), status=200)
        result = json.loads(res.text)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get("objectType", ""), "conversation")

    def test_post_message_to_inexistent_group_conversation_creates_conversation(self):
        """
            Given a plain user
            When I post a message to more than one person
            Then a new conversation is created
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)
        resp = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        self.assertEqual(resp.json['contexts'][0]['displayName'], creation_message['contexts'][0]['displayName'])

        cid = resp.json['contexts'][0]['id']
        resp = self.testapp.get('/conversations/{}'.format(cid), '', oauth2Header(sender), status=200)
        self.assertEqual(resp.json.get("tags", None), ['group'])

    def test_post_message_to_inexistent_group_conversation_with_oneself_repeated(self):
        """
            Given a plain user
            When I post a message to more than one person
            Then a new conversation is created
        """
        from .mockers import group_message_duplicated as creation_message
        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender)
        self.create_user(recipient)

        self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=400)

    def test_post_messages_to_existing_group_conversation_creates_another_conversation(self):
        """
            Given a plain user
            And a conversation between me and two other people
            When i post a message to the same group of people
            And I don't specify the existing conversation
            Then a new conversation is created
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res1 = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        import time
        time.sleep(1)
        res2 = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)

        self.assertNotEqual(res1.json['contexts'][0]['id'], res2.json['contexts'][0]['id'])

    def test_post_message_to_group_conversation_check_participants_reception(self):
        """
            Given a plain user
            And a conversation between me and two other people
            When i post a message to the conversation
            Then all participants can see the message
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        res = self.testapp.get('/conversations/{}/messages'.format(conversation_id), '', oauth2Header(recipient), status=200)
        self.assertEqual(len(res.json), 1)
        self.assertEqual(res.json[0]['contexts'][0]['id'], conversation_id)
        self.assertEqual(res.json[0]['object']['content'], creation_message['object']['content'])

        res = self.testapp.get('/conversations/{}/messages'.format(conversation_id), '', oauth2Header(recipient2), status=200)
        self.assertEqual(len(res.json), 1)
        self.assertEqual(res.json[0]['contexts'][0]['id'], conversation_id)
        self.assertEqual(res.json[0]['object']['content'], creation_message['object']['content'])

    def test_add_inexistent_participant_to_inexistent_conversation(self):
        """
            Given a plain user
            When i try to add a participant to a conversation
            And that conversation does not exists neither does the user
            Then I get an error
        """
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = "shakira"

        self.create_user(sender)
        self.create_user(recipient)

        conversation_id = '0123456789abcdef01234567'
        self.testapp.post('/people/{}/conversations/{}'.format(recipient2, conversation_id), '', oauth2Header(sender), status=400)

    def test_add_participant_to_inexistent_conversation(self):
        """
            Given a plain user
            When i try to add a participant to a conversation
            And that conversation does not exists
            Then I get an error
        """
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = "shakira"

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        conversation_id = '0123456789abcdef01234567'
        self.testapp.post('/people/{}/conversations/{}'.format(recipient2, conversation_id), '', oauth2Header(sender), status=404)

    def test_add_participant_to_conversation(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am the owner of the conversation
            When i try to add a participant to a conversation
            Then the participant joins the conversation
            And all subscriptions get updated
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        newuser = 'melendi'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)
        self.create_user(newuser)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/people/{}/conversations/{}'.format(newuser, conversation_id), '', oauth2Header(sender), status=201)
        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json['participants']), 4)

        def get_user_subscription_participants(username):
            resp = self.testapp.get('/people/{}'.format(username), '', oauth2Header(username), status=200)
            return resp.json['talkingIn'][0]['participants']

        u0_participants = get_user_subscription_participants(sender)
        u1_participants = get_user_subscription_participants(recipient)
        u2_participants = get_user_subscription_participants(recipient2)
        u3_participants = get_user_subscription_participants(newuser)

        self.assertEqual(len(u0_participants), 4)
        self.assertEqual(len(u1_participants), 4)
        self.assertEqual(len(u2_participants), 4)
        self.assertEqual(len(u3_participants), 4)

        return conversation_id, newuser

    def test_add_participant_to_two_people_conversation(self):
        """
            Given a plain user
            And a conversation between me and another user
            And I am the owner of the conversation
            When i try to add a participant to a conversation
            Then I get an error
        """
        from .mockers import message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/people/{}/conversations/{}'.format(recipient2, conversation_id), '', oauth2Header(sender), status=403)
        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json['participants']), 2)

    def test_non_owner_add_participant_to_conversation(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am not the owner of the conversation
            When i try to add a participant to a conversation
            Then I get an error
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        recipient3 = 'melendi'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)
        self.create_user(recipient3)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/people/{}/conversations/{}'.format(recipient3, conversation_id), '', oauth2Header(recipient), status=401)

    def test_conversation_participant_limit(self):
        """
            Given a plain user
            And a conversation between me and other people
            When i try to add a participant to a conversation
            And that conversation is full
            Then I get an error
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        nonallowed = 'alexis'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)
        self.create_user(nonallowed)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        limit = 20
        for i in range(limit - 3):
            newusername = 'user{}'.format(i)
            self.create_user(newusername)
            self.testapp.post('/people/{}/conversations/{}'.format(newusername, conversation_id), '', oauth2Header(sender), status=201)

        self.testapp.post('/people/{}/conversations/{}'.format(nonallowed, conversation_id), '', oauth2Header(sender), status=403)

    def test_add_existing_participant_to_conversation(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am the owner of the conversation
            When i try to add a participant to a conversation
            And that participant is already on the conversation
            Then the participant is not duplicated
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/people/{}/conversations/{}'.format(recipient2, conversation_id), '', oauth2Header(recipient), status=200)
        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json['participants']), 3)

    def test_user_leaves_two_people_conversation(self):
        """
            Given a plain user
            And a conversation between me and another user
            And I am not the owner of the conversation
            When i try to leave the conversation
            Then I am no longer in the conversation
            And the conversation is tagged as archive
        """
        from .mockers import message as creation_message
        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient, conversation_id), '', oauth2Header(recipient), status=204)
        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json['participants']), 2)
        self.assertIn('archive', res.json['tags'])
        self.assertEqual(res.json['displayName'], recipient)
        return conversation_id, sender, recipient

    def test_user_leaves_conversation(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am not the owner of the conversation
            When i try to leave the conversation
            Then I am no longer in the conversation
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient2, conversation_id), '', oauth2Header(recipient2), status=204)
        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json['participants']), 2)
        participant_usernames = [user['username'] for user in res.json['participants']]
        self.assertNotIn(recipient2, participant_usernames)

        def get_user_subscription_participants(username):
            resp = self.testapp.get('/people/{}'.format(username), '', oauth2Header(username), status=200)
            return resp.json['talkingIn'][0]['participants']

        u0_participants = get_user_subscription_participants(sender)
        u1_participants = get_user_subscription_participants(recipient)

        self.assertEqual(len(u0_participants), 2)
        self.assertEqual(len(u1_participants), 2)

    def test_users_leaves_group_conversation(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am not the owner of the conversation
            When everyone except the owner leaves the conversation
            Then only the owner remains in the conversation
            And the conversation is tagged as archived
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient, conversation_id), '', oauth2Header(recipient), status=204)
        self.testapp.delete('/people/{}/conversations/{}'.format(recipient2, conversation_id), '', oauth2Header(recipient2), status=204)
        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json['participants']), 1)
        participant_usernames = [user['username'] for user in res.json['participants']]
        self.assertNotIn(recipient2, participant_usernames)
        self.assertNotIn(recipient, participant_usernames)
        self.assertIn('archive', res.json['tags'])
        self.assertIn('group', res.json['tags'])

    def test_users_leaves_group_conversation_then_someone_rejoins(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am not the owner of the conversation
            When everyone except the owner leaves the conversation
            And then someone gets in again
            The conversation is no longer tagges as archive
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient, conversation_id), '', oauth2Header(recipient), status=204)
        self.testapp.delete('/people/{}/conversations/{}'.format(recipient2, conversation_id), '', oauth2Header(recipient2), status=204)

        # User recipient1 rejoin
        self.testapp.post('/people/{}/conversations/{}'.format(recipient, conversation_id), '', oauth2Header(sender), status=201)

        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json['participants']), 2)
        participant_usernames = [user['username'] for user in res.json['participants']]
        self.assertNotIn(recipient2, participant_usernames)
        self.assertIn('group', res.json['tags'])
        self.assertNotIn('archive', res.json['tags'])

    def test_conversation_owner_cannot_leave_conversation(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am the owner of the conversation
            When i try to leave the conversation
            I get an error
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        res = self.testapp.delete('/people/{}/conversations/{}'.format(sender, conversation_id), '', oauth2Header(sender), status=403)

    def test_conversation_owner_transfers_ownership(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am the owner of the conversation
            When i try to transfer the ownership to someone
            That someone becomes the owner
            And i'm now able to leave the conversation
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        res = self.testapp.put('/conversations/{}/owner'.format(conversation_id), json.dumps({'actor': {'username': recipient}}), oauth2Header(sender), status=200)
        self.assertEqual(res.json['owner'], recipient)

        res = self.testapp.delete('/people/{}/conversations/{}'.format(sender, conversation_id), '', oauth2Header(sender), status=204)

    def test_conversation_owner_transfers_ownership_to_user_not_in_conversation(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am the owner of the conversation
            When i try to transfer the ownership to someone
            And that someone is not on the conversation
            Then i cannon transfer the ownership
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        outsider = 'cristiano'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)
        self.create_user(outsider)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        res = self.testapp.put('/conversations/{}/owner'.format(conversation_id), json.dumps({'actor': {'username': outsider}}), oauth2Header(sender), status=404)

    def test_conversation_owner_transfers_ownership_to_inexistent_user(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am the owner of the conversation
            When i try to transfer the ownership to someone
            And that someone doesn't exists
            Then i cannon transfer the ownership
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        res = self.testapp.put('/conversations/{}/owner'.format(conversation_id), json.dumps({'actor': {'username': 'i.do.not.exist'}}), oauth2Header(sender), status=400)

    def test_conversation_non_owner_transfers_ownership(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am not the owner of the conversation
            When i try to transfer the ownership to someone
            Then i cannon transfer the ownership
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        res = self.testapp.put('/conversations/{}/owner'.format(conversation_id), json.dumps({'actor': {'username': recipient}}), oauth2Header(recipient), status=401)

    def test_non_conversation_participant_cannot_leave_conversation(self):
        """
            Given a plain user
            And a conversation between other people
            When i try to leave the conversation
            I get an error because i'm no in that conversation
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        external = 'casillas'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)
        self.create_user(external)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        res = self.testapp.delete('/people/{}/conversations/{}'.format(external, conversation_id), '', oauth2Header(sender), status=404)

    def test_user_leaves_conversation_other_participants_keep_seeing_messages(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am not the owner of the conversation
            When i leave the conversation
            Then other participants still see the left user conversation messages
        """
        from .mockers import group_message as creation_message
        from .mockers import message2
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/conversations/{}/messages'.format(conversation_id), json.dumps(message2), oauth2Header(recipient2), status=201)

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient2, conversation_id), '', oauth2Header(recipient2), status=204)
        res = self.testapp.get('/conversations/{}/messages'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json), 2)

    def test_user_leaves_conversation_cannot_see_conversation_messages(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am not the owner of the conversation
            When i leave the conversation
            I cannot longer see the conversation messages
        """
        from .mockers import group_message as creation_message
        from .mockers import message2

        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/conversations/{}/messages'.format(conversation_id), json.dumps(message2), oauth2Header(recipient2), status=201)

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient2, conversation_id), '', oauth2Header(recipient2), status=204)
        res = self.testapp.get('/conversations/{}/messages'.format(conversation_id), '', oauth2Header(recipient2), status=401)

    def test_conversation_owner_kicks_user(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am the owner of the conversation
            When i kick a user out of the conversation
            Then the user is no longer in the conversation
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient2, conversation_id), '', oauth2Header(sender), status=204)
        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(len(res.json['participants']), 2)
        participant_usernames = [user['username'] for user in res.json['participants']]
        self.assertNotIn(recipient2, participant_usernames)

        def get_user_subscription_participants(username):
            resp = self.testapp.get('/people/{}'.format(username), '', oauth2Header(username), status=200)
            return resp.json['talkingIn'][0]['participants']

        u0_participants = get_user_subscription_participants(sender)
        u1_participants = get_user_subscription_participants(recipient)

        self.assertEqual(len(u0_participants), 2)
        self.assertEqual(len(u1_participants), 2)

    def test_non_conversation_owner_kicks_user(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am not the owner of the conversation
            When i try to kick a user out of the conversation
            Then i get an error
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.delete('/people/{}/conversations/{}'.format(recipient, conversation_id), '', oauth2Header(recipient2), status=401)

    def test_conversation_owner_deletes_conversation(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am the owner of the conversation
            When i delete the conversation
            Then the conversation disappears for all users
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.delete('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=204)
        self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=404)
        self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(recipient), status=404)
        return conversation_id

    def test_conversation_messages_deleted_after_deleting_conversation(self):
        """
            Given a plain user
            And a conversation between me and other people with messages
            When the owner deletes the conversation
            Then I cannot see the conversation messages
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.delete('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=204)
        self.assertEqual(self.app.registry.max_store.messages.count(), 0)

    def test_conversation_messages_deleted_only(self):
        """
            Given a plain user
            And a conversation between me and other people with messages
            When the owner deletes the conversation
            Then the messages of other conversations still exists
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)

        self.testapp.delete('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=204)
        self.assertEqual(self.app.registry.max_store.messages.count(), 1)

    def test_non_conversation_owner_cannot_delete_conversation(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am not the owner of the conversation
            When I try to delete the conversation
            Then I get an error
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        res = self.testapp.delete('/conversations/{}'.format(conversation_id), '', oauth2Header(recipient), status=401)

    def test_conversation_owner_changes_conversation_displayName(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am the owner of the conversation
            When I change the displayName
            The conversation displayName changes
        """
        from .mockers import group_message as creation_message

        self.create_user(test_manager)
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']
        self.testapp.put('/conversations/{}'.format(conversation_id), '{"displayName": "Nou nom"}', oauth2Header(sender), status=200)
        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(res.json['displayName'], 'Nou nom')

    def test_non_conversation_owner_cannot_change_conversation_displayName(self):
        """
            Given a plain user
            And a conversation between me and other people
            And I am not the owner of the conversation
            When I try to change the displayName
            I get an error
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']
        self.testapp.put('/conversations/{}'.format(conversation_id), '{"displayName": "Nou nom"}', oauth2Header(recipient), status=401)

    def test_two_people_conversation_displayName_is_partner_displayName(self):
        """
            Given a plain user
            And a conversation between me and another user
            When I read the conversation details
            The displayName is the displayName of the other participant
        """
        from .mockers import message as creation_message
        sender = 'messi'
        recipient = 'xavi'

        self.create_user(sender, displayName='Leo Messi')
        self.create_user(recipient, displayName='Xavi Hernandez')

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(res.json['displayName'], 'Xavi Hernandez')
        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(recipient), status=200)
        self.assertEqual(res.json['displayName'], 'Leo Messi')

    def test_two_people_conversation_formerly_group_displayName_is_partner_displayName(self):
        """
            Given a plain user
            And a conversation between me and another user
            And that conversation previously was a three user conversation with a displayName
            When I read the conversation details
            The displayName is preserved
        """
        from .mockers import group_message as creation_message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender, displayName='Leo Messi')
        self.create_user(recipient, displayName='Xavi Hernandez')
        self.create_user(recipient2, displayName='La Shakira')

        res = self.testapp.post('/conversations', json.dumps(creation_message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']
        self.testapp.delete('/people/{}/conversations/{}'.format(recipient, conversation_id), '', oauth2Header(sender), status=204)

        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(sender), status=200)
        self.assertEqual(res.json['displayName'], creation_message['contexts'][0]['displayName'])
        res = self.testapp.get('/conversations/{}'.format(conversation_id), '', oauth2Header(recipient2), status=200)
        self.assertEqual(res.json['displayName'], creation_message['contexts'][0]['displayName'])

    def test_get_pushtokens_for_given_conversations(self):
        """ doctest .. http:get:: /conversations/{id}/tokens """
        from .mockers import message
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        platform = 'ios'
        token_sender = '12345678901234567890123456789012'
        token_recipient = '12345678901234567890123456789012'
        self.testapp.post('/people/%s/device/%s/%s' % (sender, platform, token_sender), "", oauth2Header(sender), status=201)
        self.testapp.post('/people/%s/device/%s/%s' % (recipient, platform, token_recipient), "", oauth2Header(recipient), status=201)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        conversation_id = res.json['contexts'][0]['id']

        res = self.testapp.get('/conversations/%s/tokens' % (conversation_id), json.dumps(message), oauth2Header(test_manager), status=200)
        self.assertEqual(res.json[0]['platform'], u'iOS')
        self.assertEqual(res.json[0]['token'], u'12345678901234567890123456789012')
        self.assertEqual(res.json[0]['username'], u'xavi')
        self.assertEqual(len(res.json), 2)
