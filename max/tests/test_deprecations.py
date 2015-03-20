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
import urlparse


class DeprecationTests(unittest.TestCase, MaxTestBase):

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

        self.create_user(test_manager)

    # Test deprecated Add people

    def test_deprecated_request_create_user(self):
        """
            Given a request to the deprecated POST /people/{username}
            When the request is processed
            Then the request is rewrited as POST /people
            And the username is now in the body
            And the displayName is preserved in the body
        """
        res = self.testapp.post('/people/sheldon', json.dumps({"displayName": 'Sheldon'}), headers=oauth2Header(test_manager), status=201)

        rewrited_request = res.request
        rewrited_request_url = urlparse.urlparse(rewrited_request.url).path
        json_body = json.loads(res.request.body)

        self.assertEqual(rewrited_request_url, '/people')
        self.assertEqual(json_body['username'], 'sheldon')
        self.assertEqual(json_body['displayName'], 'Sheldon')

    # Test deprecated subscribe user

    def test_deprecated_subscribe_user(self):
        """
            Given a request to the deprecated POST /people/{username}/subscriptions
            When the request is processed
            Then the request is rewrited as POST /contexts/{hash}/subscriptions
            And the actor now is in the body
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'

        self.create_user(username)
        res = self.create_context(create_context)
        context_hash = res.json['hash']

        res = self.testapp.post('/people/%s/subscriptions' % username, json.dumps(subscribe_context), oauth2Header(test_manager), status=201)

        rewrited_request = res.request
        rewrited_request_url = urlparse.urlparse(rewrited_request.url).path
        json_body = json.loads(res.request.body)

        self.assertEqual(rewrited_request_url, '/contexts/{}/subscriptions'.format(context_hash))
        self.assertEqual(json_body['actor']['username'], 'sheldon')
        self.assertEqual(json_body['actor']['objectType'], 'person')

    # Test deprecated create context activity

    def test_deprecated_user_post_activity_to_context(self):
        """
            Given a request to the deprecated POST /people/{username}/activities
            And the request has a "contexts" parameter
            When the request is processed
            Then the request is rewrited as POST /contexts/{hash}/activities
            And the actor is in the body
            and object is preserved in the body
        """
        from max.tests.mockers import create_context, subscribe_context
        from max.tests.mockers import user_status_context as activity

        username = 'sheldon'

        self.create_user(username)
        res = self.create_context(create_context)
        context_hash = res.json['hash']
        self.admin_subscribe_user_to_context(username, subscribe_context)

        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)

        rewrited_request = res.request
        rewrited_request_url = urlparse.urlparse(rewrited_request.url).path
        json_body = json.loads(res.request.body)

        self.assertEqual(rewrited_request_url, '/contexts/{}/activities'.format(context_hash))
        self.assertEqual(json_body['actor']['username'], 'sheldon')
        self.assertEqual(json_body['actor']['objectType'], 'person')
        self.assertIn('object', json_body)

    def test_deprecated_user_post_activity_to_context_without_context(self):
        """
            Given a request to the deprecated POST /people/{username}/activities
            And the request doesn't have a "contexts" parameter
            When the request is processed
            Then the request remains untouched
        """
        from max.tests.mockers import create_context, subscribe_context
        from max.tests.mockers import user_status as activity

        username = 'sheldon'

        self.create_user(username)
        res = self.create_context(create_context)
        context_hash = res.json['hash']
        self.admin_subscribe_user_to_context(username, subscribe_context)

        res = self.testapp.post('/people/sheldon/activities', json.dumps(activity), oauth2Header(username), status=201)

        rewrited_request = res.request
        rewrited_request_url = urlparse.urlparse(rewrited_request.url).path
        json_body = json.loads(res.request.body)

        self.assertEqual(rewrited_request_url, '/people/sheldon/activities'.format(context_hash))
        self.assertNotIn('actor', json_body)



