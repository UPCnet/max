# -*- coding: utf-8 -*-
import os
import json
import unittest
from functools import partial

from paste.deploy import loadapp
from mock import patch
from maxrules import config

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header, mock_post, mock_get
from max.tests import test_default_security

config.mongodb_db_name = 'tests'


class RulesTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_get = patch('requests.get', new=partial(mock_get, self))
        self.patched_get.start()
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

    # BEGIN TESTS

    def test_process_new_tweet_from_hashtag(self):
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, subscribe_contextA
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi", "twitterUsername": "leomessi"})
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterHashtag": "assignatura1"})
        self.admin_subscribe_user_to_context(username, subscribe_contextA)

        processTweet('leomessi', u'Ehteee, acabo de batir el récor de goles en el Barça #upc #assignatura1')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

    def test_process_new_tweet_from_hashtag_to_unsubscribed_context(self):
        from maxrules.tasks import processTweet
        from .mockers import create_contextA
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi", "twitterUsername": "leomessi"})
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterHashtag": "assignatura1"})

        processTweet('leomessi', u'Ehteee, acabo de batir el récor de goles en el Barça #upc #assignatura1')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 0)

    def test_process_new_tweet_from_double_registered_hashtag_subscribed_only_on_newest(self):
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, create_contextB
        from .mockers import subscribe_contextB
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi", "twitterUsername": "leomessi"})
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')

        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterHashtag": "assignatura1"})

        self.create_context(create_contextB, permissions=context_permissions)
        self.modify_context(create_contextB['url'], {"twitterHashtag": "assignatura1"})

        self.admin_subscribe_user_to_context(username, subscribe_contextB)

        processTweet('leomessi', u'Ehteee, acabo de batir el récor de goles en el Barça #upc #assignatura1')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextB['object']['url'])

    def test_process_new_tweet_from_double_registered_hashtag_subscribed_only_on_oldest(self):
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, create_contextB
        from .mockers import subscribe_contextA
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi", "twitterUsername": "leomessi"})
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')

        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterHashtag": "assignatura1"})

        self.create_context(create_contextB, permissions=context_permissions)
        self.modify_context(create_contextB['url'], {"twitterHashtag": "assignatura1"})

        self.admin_subscribe_user_to_context(username, subscribe_contextA)

        processTweet('leomessi', u'Ehteee, acabo de batir el récor de goles en el Barça #upc #assignatura1')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

    def test_process_new_tweet_from_double_registered_hashtag_subscribed_in_both(self):
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, create_contextB
        from .mockers import subscribe_contextA, subscribe_contextB
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi", "twitterUsername": "leomessi"})
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')

        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterHashtag": "assignatura1"})
        self.admin_subscribe_user_to_context(username, subscribe_contextA)

        self.create_context(create_contextB, permissions=context_permissions)
        self.modify_context(create_contextB['url'], {"twitterHashtag": "assignatura1"})
        self.admin_subscribe_user_to_context(username, subscribe_contextB)

        processTweet('leomessi', u'Ehteee, acabo de batir el récor de goles en el Barça #upc #assignatura1')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextB['object']['url'])
        self.assertEqual(result[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[1].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

    def test_process_new_tweet_from_hashtag_uppercase_from_twitter(self):
        """
        Test the case where we lower the case of the hashtag to match the lowercased from uppercase,
        which whe know it's in database
        """
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, subscribe_contextA
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi", "twitterUsername": "leomessi"})
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterHashtag": "assignatura1"})
        self.admin_subscribe_user_to_context(username, subscribe_contextA)

        processTweet('leomessi', u'Ehteee, acabo de batir el récor de goles en el Barça #UPC #ASSIGNATURA1')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

    def test_process_new_tweet_from_twitter_username_uppercase_case_from_twitter(self):
        """
        Test the case where we lower the case of the username to match the lowercased from uppercase,
        which whe know it's in database
        """
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, subscribe_contextA
        username = 'messi'
        self.create_user(username)
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterUsername": "MaxUpcnet"})
        self.admin_subscribe_user_to_context(username, subscribe_contextA)
        processTweet('MAXUPCNET', u'Ehteee, acabo de batir el récor de goles en el Barça.')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('actor', None).get('url'), subscribe_contextA['object']['url'])
        self.assertEqual(result[0].get('actor', None).get('objectType'), 'uri')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

    def test_process_new_tweet_from_twitter_username_different_case_in_max(self):
        """
        Test the case where we create a user with specific letter-case-setting twitter username associated, and we try
        to match it with a tweet with username that is different in letter-case
        """
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, subscribe_contextA
        username = 'messi'
        self.create_user(username)
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterUsername": "MaxUpcnet"})
        self.admin_subscribe_user_to_context(username, subscribe_contextA)

        processTweet('maxUpcnet', u'Ehteee, acabo de batir el récor de goles en el Barça.')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('actor', None).get('url'), subscribe_contextA['object']['url'])
        self.assertEqual(result[0].get('actor', None).get('objectType'), 'uri')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

    def test_process_new_tweet_from_hashtag_different_case_in_max(self):
        """
        Test the case where we create a context with a specific case setting hashtag associated, and we try
        to match it with a tweet that is different in letter-case.
        """
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, subscribe_contextA
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi", "twitterUsername": "leomessi"})
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterHashtag": "Assignatura1"})
        self.admin_subscribe_user_to_context(username, subscribe_contextA)

        processTweet('leomessi', u'Ehteee, acabo de batir el récor de goles en el Barça #UPC #assignaTURA1')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

    def test_process_new_tweet_from_unassociated_user(self):
        """
        Test the case where we receive a valid tweet, but there's no user associated with the hashtag
        """
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, subscribe_contextA
        username = 'messi'
        self.create_user(username)
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterHashtag": "Assignatura1"})
        self.admin_subscribe_user_to_context(username, subscribe_contextA)

        processTweet('leomessi', u'Ehteee, acabo de batir el récor de goles en el Barça #UPC #Assignatura1')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 0)

    def test_process_new_tweet_from_unassociated_context(self):
        """
        Test the case where we receive a valid tweet, but there's no user associated with the hashtag
        """
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, subscribe_contextA
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi", "twitterUsername": "leomessi"})
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_contextA, permissions=context_permissions)
        self.admin_subscribe_user_to_context(username, subscribe_contextA)

        processTweet('leomessi', u'Ehteee, acabo de batir el récor de goles en el Barça #UPC #Assignatura1')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 0)

    def test_process_tweet_from_debug_hashtag(self):
        """
        Test the case when we reiceive a valid tweet with a debug hashtag
        """
        from maxrules.tasks import processTweet
        from maxrules.twitter import debug_hashtag
        from .mockers import create_contextA, subscribe_contextA
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi", "twitterUsername": "leomessi"})
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterHashtag": "Assignatura1"})
        self.admin_subscribe_user_to_context(username, subscribe_contextA)

        processTweet('leomessi', u'Ehteee, acabo de batir el récor de goles en el Barça #%s #Assignatura1' % (debug_hashtag))
        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 0)
