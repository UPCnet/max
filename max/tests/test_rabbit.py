# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from maxcarrot import RabbitClient

from functools import partial
from mock import patch
from paste.deploy import loadapp

import new
import os
import sys
import unittest
from time import sleep

skipRabbitTest = partial(
    unittest.skipUnless,
    os.environ.get('rabbit', False),
    'Skipping due to lack of a Rabbitmq Server'
)


def get_module(name):
    return sys.modules[name]


def import_object(module__name, dotted):
    last = get_module(module__name)
    parts = dotted.split('.')
    for part in parts:
        last = getattr(last, part)
    return last


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:rabbitmq.ini', relative_to=conf_dir)
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

        # Rabbitmq test client initialization
        rabbitmq_url = self.app.registry.settings['max.rabbitmq']
        self.server = RabbitClient(rabbitmq_url)
        self.server.management.cleanup(delete_all=True)
        self.server.declare()

    def tearDown(self):
        import pyramid.testing
        pyramid.testing.tearDown()
        self.server.disconnect()

    def run_test(self, test_module_name, test_name):
        """
            Runs a test method from another module in a dirty (but awesome) way
        """
        method_dotted_name = '{}.FunctionalTests.{}'.format(test_module_name, test_name)
        test_method = import_object('max.tests', method_dotted_name)

        # Create a new function sharing code, name and current globals
        # plus other imports needed by other modules
        current_globals = globals()
        current_globals.update({
            'json': get_module('json'),
            'oauth2Header': import_object('max.tests', 'base.oauth2Header'),
            'test_manager': import_object('max.tests', 'test_manager')
        })

        wrapped_test_method = new.function(test_method.func_code, current_globals, test_method.func_name)

        # execute the new method and return result (if any)
        return wrapped_test_method(self)

    # All tests within this module executes code from tests on other modules
    # As this module has rabbitmq activated in the ini, each test should produce
    # rabbitmq associated actions, coded with each tested codebase, so we just
    # execute the code, and check for the existence of the desired structures.
    #
    # NOTE that we may expect return values from the test, to know which values
    # the test produced. Please modify used tests to return those values if needed.

    @skipRabbitTest()
    def test_create_user_bindings(self):
        username = self.run_test('test_people', 'test_create_user')

        self.server.management.load_exchanges()
        self.assertIn('{}.publish'.format(username), self.server.management.exchanges_by_name)
        self.assertIn('{}.subscribe'.format(username), self.server.management.exchanges_by_name)

    @skipRabbitTest()
    def test_create_user_without_bindings(self):
        username = 'messi'
        self.create_user(username, qs_params={"notifications": False})

        self.server.management.load_exchanges()
        self.assertNotIn('{}.publish'.format(username), self.server.management.exchanges_by_name)
        self.assertNotIn('{}.subscribe'.format(username), self.server.management.exchanges_by_name)

    @skipRabbitTest()
    def test_create_existing_user_dont_create_bindings(self):
        """
            Given a created user without rabbitmq exchanges
            When i try to create the user again
            The exchanges won't be created
        """
        username = 'messi'
        self.create_user(username, qs_params={"notifications": False})
        self.create_user(username, expect=200)

        self.server.management.load_exchanges()
        self.assertNotIn('{}.publish'.format(username), self.server.management.exchanges_by_name)
        self.assertNotIn('{}.subscribe'.format(username), self.server.management.exchanges_by_name)

    @skipRabbitTest()
    def test_create_existing_user_create_bindings(self):
        """
            Given a created user without rabbitmq exchanges
            When i try to create the user again
            And i explicitly request to create exchanges for notifications
            The exchanges will be created
        """
        username = 'messi'
        self.create_user(username, qs_params={"notifications": False})
        self.create_user(username, qs_params={"notifications": True}, expect=200)

        self.server.management.load_exchanges()
        self.assertIn('{}.publish'.format(username), self.server.management.exchanges_by_name)
        self.assertIn('{}.subscribe'.format(username), self.server.management.exchanges_by_name)

    @skipRabbitTest()
    def test_self_create_existing_user_dont_create_bindings(self):
        """
            Given a created user without rabbitmq exchanges
            When i try to create the user again
            The exchanges won't be created
        """
        username = 'messi'
        self.create_user(username, qs_params={"notifications": False}, creator=username)
        self.create_user(username, expect=200, creator=username)

        self.server.management.load_exchanges()
        self.assertNotIn('{}.publish'.format(username), self.server.management.exchanges_by_name)
        self.assertNotIn('{}.subscribe'.format(username), self.server.management.exchanges_by_name)

    @skipRabbitTest()
    def test_self_create_existing_user_create_bindings(self):
        """
            Given a created user without rabbitmq exchanges
            When i try to create the user again
            And i explicitly request to create exchanges for notifications
            The exchanges will be created
        """
        username = 'messi'
        self.create_user(username, qs_params={"notifications": False}, creator=username)
        self.create_user(username, qs_params={"notifications": True}, expect=200, creator=username)

        self.server.management.load_exchanges()
        self.assertIn('{}.publish'.format(username), self.server.management.exchanges_by_name)
        self.assertIn('{}.subscribe'.format(username), self.server.management.exchanges_by_name)

    @skipRabbitTest()
    def test_create_conversation_bindings(self):
        cid, creator = self.run_test('test_conversations', 'test_post_message_to_conversation_check_conversation')

        # Find defined bindings for this conversation
        bindings = self.server.management.load_exchange_bindings('conversations')
        bindings = [bind for bind in bindings if ".*".format(cid) in bind['routing_key']]

        self.assertEqual(len(bindings), 4)

    @skipRabbitTest()
    def test_create_conversation_check_notification(self):
        cid, creator = self.run_test('test_conversations', 'test_post_message_to_conversation_check_conversation')

        sleep(0.1)

        messages_to_push_queue = self.server.get_all('push')
        self.assertEqual(len(messages_to_push_queue), 1)

        carrot_message, haigha_message = messages_to_push_queue[0]
        self.assertEqual(haigha_message.delivery_info['routing_key'], '{}.notifications'.format(cid))
        self.assertEqual(carrot_message['a'], 'a')
        self.assertEqual(carrot_message['o'], 'c')
        self.assertEqual(carrot_message['u']['u'], creator)
        self.assertEqual(carrot_message['u']['d'], creator)

    @skipRabbitTest()
    def test_delete_conversation_bindings(self):
        cid = self.run_test('test_conversations', 'test_conversation_owner_deletes_conversation')

        # Find defined bindings for this conversation
        bindings = self.server.management.load_exchange_bindings('conversations')
        bindings = [bind for bind in bindings if ".*".format(cid) in bind['routing_key']]

        self.assertEqual(len(bindings), 0)

    @skipRabbitTest()
    def test_remove_user_from_conversation_bindings(self):
        cid, userin, userout = self.run_test('test_conversations', 'test_user_leaves_two_people_conversation')

        # Find defined bindings for this conversation
        bindings = self.server.management.load_exchange_bindings('conversations')
        bindings = [bind for bind in bindings if ".*".format(cid) in bind['routing_key']]

        # Search for the bindings of the user still on the conversation
        userin_bindings = [
            bind for bind in bindings
            if "{}.publish".format(userin) == bind['source']
            or "{}.subscribe".format(userin) == bind['destination']
        ]

        # search for the bindings of the user that left the conversation
        userout_bindings = [
            bind for bind in bindings
            if "{}.publish".format(userout) == bind['source']
            or "{}.subscribe".format(userout) == bind['destination']
        ]

        self.assertEqual(len(bindings), 2)
        self.assertEqual(len(userin_bindings), 2)
        self.assertEqual(len(userout_bindings), 0)

    @skipRabbitTest()
    def test_add_new_user_to_conversation_bindings(self):
        cid, newuser = self.run_test('test_conversations', 'test_add_participant_to_conversation')

        # Find defined bindings for this conversation
        bindings = self.server.management.load_exchange_bindings('conversations')
        bindings = [bind for bind in bindings if ".*".format(cid) in bind['routing_key']]

        # Search for the bindings of the user still on the conversation
        newuser_bindings = [
            bind for bind in bindings
            if "{}.publish".format(newuser) == bind['source']
            or "{}.subscribe".format(newuser) == bind['destination']
        ]

        self.assertEqual(len(bindings), 8)
        self.assertEqual(len(newuser_bindings), 2)

    @skipRabbitTest()
    def test_delete_context_bindings(self):
        context_hash = self.run_test('test_contexts_notifications', 'test_delete_context_with_notifications_removes_subscriptions')

        # Find defined bindings for this context
        bindings = self.server.management.load_exchange_bindings('activity')
        bindings = [bind for bind in bindings if ".*".format(context_hash) in bind['routing_key']]

        self.assertEqual(len(bindings), 0)

    @skipRabbitTest()
    def test_add_user_subscription_bindings(self):
        context_hash, subscribed_user = self.run_test('test_contexts_notifications', 'test_subscribe_user_to_context_with_notifications')

        # Find defined bindings for this context
        bindings = self.server.management.load_exchange_bindings('activity')
        bindings = [bind for bind in bindings if context_hash in bind['routing_key']]

        # Search for the bindings of the user still on the conversation
        subscribed_bindings = [
            bind for bind in bindings
            if "{}.subscribe".format(subscribed_user) == bind['destination']
        ]

        self.assertEqual(len(bindings), 1)
        self.assertEqual(len(subscribed_bindings), 1)

    @skipRabbitTest()
    def test_remove_user_subscription_bindings(self):
        context_hash, unsubscribed_user = self.run_test('test_contexts_notifications', 'test_unsubscribe_user_from_context_with_notifications')

        # Find defined bindings for this context
        bindings = self.server.management.load_exchange_bindings('activity')
        bindings = [bind for bind in bindings if context_hash in bind['routing_key']]

        # Search for the bindings of the user still on the conversation
        unsubscribed_bindings = [
            bind for bind in bindings
            if "{}.subscribe".format(unsubscribed_user) == bind['destination']
        ]

        self.assertEqual(len(bindings), 0)
        self.assertEqual(len(unsubscribed_bindings), 0)

    @skipRabbitTest()
    def test_post_message_check_notification(self):
        cid, creator, activity = self.run_test('test_contexts_notifications', 'test_post_activity_on_context_with_notifications')

        sleep(0.1)

        messages_to_push_queue = self.server.get_all('push')
        carrot_message, haigha_message = messages_to_push_queue[0]

        self.assertEqual(len(messages_to_push_queue), 1)
        self.assertEqual(haigha_message.delivery_info['routing_key'], '{}'.format(cid))
        self.assertEqual(carrot_message['a'], 'a')
        self.assertEqual(carrot_message['o'], 'a')
        self.assertEqual(carrot_message['u']['u'], creator)
        self.assertEqual(carrot_message['u']['d'], creator)
        self.assertEqual(carrot_message['d']['text'].encode('utf-8'), activity['object']['content'])

    @skipRabbitTest()
    def test_post_message_check_no_notification(self):
        cid, creator, activity = self.run_test('test_contexts', 'test_post_activity_with_private_read_write_context')

        messages_to_push_queue = self.server.get_all('push')
        self.assertEqual(len(messages_to_push_queue), 0)

    @skipRabbitTest()
    def test_post_comment_check_notification(self):
        cid, creator, activity, comment = self.run_test('test_contexts_notifications', 'test_post_comment_with_comments_notification')

        sleep(0.1)

        messages_to_push_queue = self.server.get_all('push')
        self.assertEqual(len(messages_to_push_queue), 2)

        carrot_message, haigha_message = messages_to_push_queue[0]

        self.assertEqual(haigha_message.delivery_info['routing_key'], '{}'.format(cid))
        self.assertEqual(carrot_message['a'], 'a')
        self.assertEqual(carrot_message['o'], 'a')
        self.assertEqual(carrot_message['u']['u'], creator)
        self.assertEqual(carrot_message['u']['d'], creator)
        self.assertEqual(carrot_message['d']['text'].encode('utf-8'), activity['object']['content'])

        carrot_message, haigha_message = messages_to_push_queue[1]

        self.assertEqual(haigha_message.delivery_info['routing_key'], '{}'.format(cid))
        self.assertEqual(carrot_message['a'], 'a')
        self.assertEqual(carrot_message['o'], 'a')
        self.assertEqual(carrot_message['u']['u'], creator)
        self.assertEqual(carrot_message['u']['d'], creator)
        self.assertEqual(carrot_message['d']['text'].encode('utf-8'), comment['object']['content'])
