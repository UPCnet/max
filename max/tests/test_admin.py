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
        self.reset_database(self.app)
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)

    # BEGIN TESTS
    def test_get_all_users_admin(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/people', "", oauth2Header(test_manager))

        self.assertEqual(len(res.json), 2)
        self.assertEqual(res.json[0].get('username'), 'test_manager')
        self.assertEqual(res.json[1].get('username'), 'messi')

    def test_admin_post_activity_without_context(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(user_status), oauth2Header(test_manager))
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None), None)

    def test_admin_post_activity_with_context(self):
        """ doctest .. http:post:: /people/{username}/activities """
        from .mockers import subscribe_context
        from .mockers import user_status_context
        from .mockers import create_context

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(user_status_context), oauth2Header(test_manager))
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], subscribe_context['object']['url'])

    def test_admin_post_activity_with_context_as_actor(self):
        """ doctest .. http:post:: /contexts/{hash}/activities """
        from .mockers import subscribe_context
        from .mockers import user_status_as_context
        from .mockers import create_context
        from hashlib import sha1
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.post('/contexts/%s/activities' % url_hash, json.dumps(user_status_as_context), oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('hash', None), url_hash)
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], subscribe_context['object']['url'])

    def test_get_other_activities(self):
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)
        self.testapp.get('/people/%s/activities' % (username), '', oauth2Header(test_manager), status=200)

    def test_delete_user(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.delete('/people/%s' % username, '', oauth2Header(test_manager), status=204)

    def test_delete_all_conversations(self):
        from .mockers import group_message as message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'

        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)

        self.testapp.delete('/conversations', '', oauth2Header(test_manager), status=204)

        conversations = self.testapp.get('/conversations', '', oauth2Header(sender), status=200)
        self.assertEqual(len(conversations.json), 0)

        user_data = self.testapp.get('/people/{}'.format(sender), '', oauth2Header(sender), status=200)
        self.assertEqual(len(user_data.json['talkingIn']), 0)

    def test_delete_inexistent_user(self):
        username = 'messi'
        username2 = 'xavi'
        self.create_user(username)
        self.testapp.delete('/people/%s' % username2, '', oauth2Header(test_manager), status=400)

    def test_admin_delete_inexistent_activity(self):
        fake_id = '519200000000000000000000'
        self.testapp.delete('/activities/%s' % (fake_id), '', oauth2Header(test_manager), status=404)

    def test_admin_get_people_activities_by_context(self):
        """
        """
        from .mockers import user_status
        from .mockers import context_query
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username, user_status)

        res = self.testapp.get('/people/%s/activities' % username, context_query, oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)

    def test_admin_get_all_activities_by_context(self):
        """




        XXX This test was here to test the Manager endpoint that didn't search for recursive activities
        now this is unified so this feature will have to be refactored to a preset or parameter to
        disable recursivity.

        The test now is fixed to pass with correct acitivity count asserts




        """
        from .mockers import user_status
        from .mockers import subscribe_context, subscribe_contextA
        from .mockers import create_context, create_contextA
        from .mockers import user_status_context, user_status_contextA

        from hashlib import sha1

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        url_hash = sha1(create_context['url']).hexdigest()

        self.create_context(create_contextA, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_contextA)
        url_hashA = sha1(create_contextA['url']).hexdigest()

        self.create_activity(username, user_status_context)
        self.create_activity(username, user_status_contextA)
        self.create_activity(username, user_status)

        res = self.testapp.get('/contexts/%s/activities' % url_hash, {}, oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 2)

        res = self.testapp.get('/contexts/%s/activities' % url_hashA, {}, oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)

    # def test_admin_post_activity_with_unauthorized_context_type_as_actor(self):
    #     from .mockers import create_unauthorized_context
    #     from hashlib import sha1

    #     result = self.create_context(create_invalid_context, expect=201)
        # url_hash = sha1(create_invalid_context['object']['url']).hexdigest()
        # res = self.testapp.post('/contexts/%s/activities' % url_hash, json.dumps(user_status_context), oauth2Header(test_manager))
        # result = json.loads(res.text)
        # self.assertEqual(result.get('actor', None).get('hash', None), url_hash)
        # self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        # self.assertEqual(result.get('contexts', None)[0], subscribe_context['object'])

    def test_get_users_twitter_enabled(self):
        """ Doctest .. http:get:: /people """
        username = 'messi'
        username2 = 'xavi'
        self.create_user(username)
        self.create_user(username2)
        self.modify_user(username, {"twitterUsername": "messipowah"})
        res = self.testapp.get('/people', {"twitter_enabled": True}, oauth2Header(test_manager), status=200)

        self.assertEqual(len(res.json), 1)

    def test_get_context_twitter_enabled(self):
        from .mockers import create_context, create_contextA
        self.create_context(create_context)
        self.create_context(create_contextA)
        self.modify_context(create_context['url'], {"twitterHashtag": "assignatura1", "twitterUsername": "maxupcnet"})

        res = self.testapp.get('/contexts', {"twitter_enabled": True}, oauth2Header(test_manager), status=200)

        self.assertEqual(len(res.json), 1)

    def test_rename_context_url(self):
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context
        from hashlib import sha1

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity = self.create_activity(username, user_status_context)

        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"url": "http://new.url"}), oauth2Header(test_manager), status=200)

        # Test context is updated
        new_url_hash = sha1('http://new.url').hexdigest()
        res = self.testapp.get('/contexts/%s' % new_url_hash, "", oauth2Header(test_manager), status=200)
        self.assertEqual(res.json['url'], 'http://new.url')
        self.assertEqual(res.json['hash'], new_url_hash)

        # Test user subscription is updated
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(test_manager), status=200)
        self.assertEqual(res.json['subscribedTo'][0]['url'], 'http://new.url')
        self.assertEqual(res.json['subscribedTo'][0]['hash'], new_url_hash)

        # Test user original subscription activity is updated
        subscription_activity = self.exec_mongo_query('activity', 'find', {'object.hash': new_url_hash, 'object.url': "http://new.url", 'actor.username': username})
        self.assertNotEqual(subscription_activity, [])
        self.assertEqual(subscription_activity[0]['object']['hash'], new_url_hash)
        self.assertEqual(subscription_activity[0]['object']['url'], 'http://new.url')

        # Test user activity is updated
        res = self.testapp.get('/activities/%s' % activity.json['id'], "", oauth2Header(test_manager), status=200)
        self.assertEqual(res.json['contexts'][0]['url'], 'http://new.url')
        self.assertEqual(res.json['contexts'][0]['hash'], new_url_hash)
