# -*- coding: utf-8 -*-
import os
import unittest
from functools import partial

from paste.deploy import loadapp
from mock import patch

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header, mock_post
from max.tests import test_manager, test_default_security
from maxcarrot import RabbitClient

skipRabbitTest = partial(
    unittest.skipUnless,
    os.environ.get('Rabbit', False),
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

    # BEGIN TESTS

    @skipRabbitTest()
    def test_create_user(self):
        username = 'messi'
        self.testapp.post('/people/%s' % username, "", oauth2Header(test_manager), status=201)
        self.server.management.load_exchanges()
        self.assertIn('messi.publish', self.server.management.exchanges_by_name)
        self.assertIn('messi.subscribe', self.server.management.exchanges_by_name)
