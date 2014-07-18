# -*- coding: utf-8 -*-
import os
import unittest
from functools import partial

from paste.deploy import loadapp
from mock import patch

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header, mock_post
from max.tests import test_manager, test_default_security
from maxcarrot import RabbitClient
import new
import sys
import json

skipRabbitTest = partial(
    unittest.skipUnless,
    os.environ.get('rabbit', False),
    'Skipping due to lack of a Rabbitmq Server'
)


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

        # Step by step import the module, class and method objects
        test_module = getattr(sys.modules['max.tests'], test_module_name)
        test_class = getattr(test_module, 'FunctionalTests')
        test_method = getattr(test_class, test_name)

        # Create a new function sharing code, name and current globals
        wrapped_test_method = new.function(test_method.func_code, globals(), test_method.func_name)

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
    def test_create_conversation_bindings(self):
        cid = self.run_test('test_conversations', 'test_post_message_to_conversation_check_conversation')

        # Find defined bindings for this conversation
        bindings = self.server.management.load_exchange_bindings('conversations')
        bindings = [bind for bind in bindings if ".*".format(cid) in bind['routing_key']]

        self.assertEqual(len(bindings), 4)

    @skipRabbitTest()
    def test_delete_conversation_bindings(self):
        cid = self.run_test('test_conversations', 'test_conversation_owner_deletes_conversation')
        # Find defined bindings for this conversation
        bindings = self.server.management.load_exchange_bindings('conversations')
        bindings = [bind for bind in bindings if ".*".format(cid) in bind['routing_key']]

        self.assertEqual(len(bindings), 0)

    @skipRabbitTest()
    def test_remove_user_bindings(self):
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
    def test_add_user_bindings(self):
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
    def test_create_context_bindings(self):
        cid = self.run_test('test_conversations', 'test_post_message_to_conversation_check_conversation')

        # Find defined bindings for this conversation
        bindings = self.server.management.load_exchange_bindings('conversations')
        bindings = [bind for bind in bindings if ".*".format(cid) in bind['routing_key']]

        self.assertEqual(len(bindings), 4)

    # @skipRabbitTest()
    # def test_delete_context_bindings(self):
    #     result = self.run_test('test_contexts', 'test_')

    # @skipRabbitTest()
    # def test_add_user_subscription_bindings(self):
    #     result = self.run_test('test_', 'test_')

    # @skipRabbitTest()
    # def test_remove_user_subscription_bindings(self):
    #     result = self.run_test('test_', 'test_')
