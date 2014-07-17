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

        # Create a new function sharin code, name and current globals
        wrapped_test_method = new.function(test_method.func_code, globals(), test_method.func_name)

        # execute the new method
        wrapped_test_method(self)

    # BEGIN TESTS

    @skipRabbitTest()
    def test_create_user(self):
        self.run_test('test_people', 'test_create_user')

        self.server.management.load_exchanges()
        self.assertIn('messi.publish', self.server.management.exchanges_by_name)
        self.assertIn('messi.subscribe', self.server.management.exchanges_by_name)
