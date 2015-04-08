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
        self.reset_database(self.app)
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

        self.assertEqual(rewrited_request_url, '/people')
        self.assertEqual(res.json['username'], 'sheldon')
        self.assertEqual(res.json['displayName'], 'Sheldon')

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

        self.assertEqual(rewrited_request_url, '/contexts/{}/subscriptions'.format(context_hash))
        self.assertEqual(res.json['actor']['username'], 'sheldon')
        self.assertEqual(res.json['actor']['objectType'], 'person')

    # Test deprecated unsubscribe user

    def test_deprecated_unsubscribe_user(self):
        """
            Given a request to the deprecated DELETE /people/{username}/subscriptions
            When the request is processed
            Then the request is rewrited as DELETE /contexts/{hash}/subscriptions
            And the actor now is in the body
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'

        self.create_user(username)
        res = self.create_context(create_context)
        context_hash = res.json['hash']

        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.testapp.delete('/people/%s/subscriptions/%s' % (username, context_hash), "", oauth2Header(test_manager), status=204)

        rewrited_request = res.request
        rewrited_request_url = urlparse.urlparse(rewrited_request.url).path

        self.assertEqual(rewrited_request_url, '/contexts/{}/subscriptions/{}'.format(context_hash, username))

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

        self.assertEqual(rewrited_request_url, '/contexts/{}/activities'.format(context_hash))
        self.assertEqual(res.json['actor']['username'], 'sheldon')
        self.assertEqual(res.json['actor']['objectType'], 'person')
        self.assertIn('object', res.json)

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

        self.assertEqual(rewrited_request_url, '/people/sheldon/activities'.format(context_hash))
        self.assertNotIn('contexts', res.json)

    # Test depreacted join conversation

    def test_deprecated_join_conversation(self):
        """
            Given a request to the deprecated POST /people/{user}/conversations/{id}
            When the request is processed
            Then the request is rewrited as DELETE /conversations/{id}/participants
            And the actor is in the body
        """
        from max.tests.mockers import group_message as message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        recipient3 = 'melendi'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)
        self.create_user(recipient3)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        res = self.testapp.post('/people/{}/conversations/{}'.format(recipient3, cid), '', oauth2Header(test_manager), status=201)

        rewrited_request = res.request
        rewrited_request_url = urlparse.urlparse(rewrited_request.url).path

        self.assertEqual(rewrited_request_url, '/conversations/{}/participants'.format(cid))
        self.assertEqual(res.json['actor']['username'], recipient3)
        self.assertEqual(res.json['actor']['objectType'], 'person')

    def test_deprecated_leave_conversation(self):
        """
            Given a request to the deprecated DELETE /people/{user}/conversations/{id}
            When the request is processed
            Then the request is rewrited as DELETE /conversations/{id}/participants/{username}
            And the url parameters are remapped
        """
        from max.tests.mockers import group_message as message
        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])

        res = self.testapp.delete('/people/{}/conversations/{}'.format(recipient2, cid), '', oauth2Header(test_manager), status=204)

        rewrited_request = res.request
        rewrited_request_url = urlparse.urlparse(rewrited_request.url).path

        self.assertEqual(rewrited_request_url, '/conversations/{}/participants/{}'.format(cid, recipient2))

    def test_deprecated_add_token(self):
        """
            Given a request to the deprecated POST /people/{user}/device/{platform}/{token}
            When the request is processed
            Then the request is rewrited as POST /tokens
            And the token is injected in the body
            And the platform is injected in the body
        """
        username = 'sheldon'
        self.create_user(username)
        token = '000000000000000000'
        platform = 'ios'

        res = self.testapp.post('/people/{}/device/{}/{}'.format(username, platform, token), '', headers=oauth2Header(username), status=201)

        rewrited_request = res.request
        rewrited_request_url = urlparse.urlparse(rewrited_request.url).path

        self.assertEqual(rewrited_request_url, '/tokens')
        self.assertEqual(res.json['token'], token)
        self.assertEqual(res.json['platform'], platform)

    def test_deprecated_delete_token(self):
        """
            Given a request to the deprecated DELETE /people/{user}/device/{platform}/{token}
            When the request is processed
            Then the request is rewrited as DELETE /tokens/{token}
            And the token is injected in the body
            And the platform is injected in the body
        """
        username = 'sheldon'
        self.create_user(username)
        token = '000000000000000000'
        platform = 'ios'

        self.testapp.post('/people/{}/device/{}/{}'.format(username, platform, token), '', headers=oauth2Header(username), status=201)
        res = self.testapp.delete('/people/{}/device/{}/{}'.format(username, platform, token), '', headers=oauth2Header(username), status=204)

        rewrited_request = res.request
        rewrited_request_url = urlparse.urlparse(rewrited_request.url).path

        self.assertEqual(rewrited_request_url, '/tokens/{}'.format(token))

    def test_deprecated_sortBy_parameter(self):
        """
            Given a plain user
            When I query ativities using old sortBy parameter
            I get the expected result

            THIS TEST IS A DUPLICATE OF max.tests.test_timeline_order_sorted_by_last_comment_publish_date
            ONLY TO TEST THE TRANSLATION OF THE SORTBY PARAMETER

        """
        from .mockers import user_status, user_comment
        username = 'messi'
        self.create_user(username)
        activity_ids = []
        # Create 7 activities to overpass limit of 5
        for i in range(7):
            activity_ids.append(self.create_activity(username, user_status, note=str(i)).json['id'])
        res = self.testapp.post('/activities/%s/comments' % str(activity_ids[0]), json.dumps(user_comment), oauth2Header(username), status=201)
        # Get first 5 results
        res = self.testapp.get('/people/%s/timeline?sortBy=comments&limit=5' % username, "", oauth2Header(username), status=200)
        self.assertEqual(len(res.json), 5)

        self.assertEqual(res.json[0].get('id', None), activity_ids[0])
        self.assertEqual(res.json[1].get('id', None), activity_ids[6])
        self.assertEqual(res.json[2].get('id', None), activity_ids[5])
        self.assertEqual(res.json[3].get('id', None), activity_ids[4])
        self.assertEqual(res.json[4].get('id', None), activity_ids[3])

        # get next 2 results
        res = self.testapp.get('/people/%s/timeline?sortBy=comments&limit=5&before=%s' % (username, activity_ids[3]), "", oauth2Header(username), status=200)
        self.assertEqual(len(res.json), 2)

        self.assertEqual(res.json[0].get('id', None), activity_ids[2])
        self.assertEqual(res.json[1].get('id', None), activity_ids[1])
