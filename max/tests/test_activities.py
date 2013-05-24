# -*- coding: utf-8 -*-
import os
import json
import unittest

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header
from max.tests import test_manager, test_default_security


class mock_post(object):

    def __init__(self, *args, **kwargs):
        pass  # pragma: no cover

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
        self.testapp = MaxTestApp(self)

    # BEGIN TESTS

    def test_create_activity(self):
        """ doctest .. http:post:: /people/{username}/activities """
        from .mockers import user_status as activity
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)

    def test_create_activity_check_ownership(self):
        """
            Given a plain user
            When I post an activity
            And I am authenticated as myself
            Then the actor,the creator and the owner must be the same
        """
        from .mockers import user_status as activity
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)
        self.assertEqual(res.json['actor']['username'], res.json['creator'])
        self.assertEqual(res.json['owner'], res.json['creator'])

    def test_delete_own_activity(self):
        """
            Given a plain user
            When I post an activity
            Then I can delete my activity
        """
        from .mockers import user_status as activity
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)
        self.testapp.delete('/activities/%s' % res.json['id'], '', oauth2Header(username), status=204)

    def test_delete_other_activity(self):
        """
            Given a plain user
            When someone else posts an activity
            Then I can't delete his activity
        """
        from .mockers import user_status as activity
        username = 'messi'
        username2 = 'xavi'
        self.create_user(username)
        self.create_user(username2)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)
        self.testapp.delete('/activities/%s' % res.json['id'], '', oauth2Header(username2), status=401)

    def test_create_activity_check_impersonated_ownership(self):
        """
            Given a admin user
            When I post an activity in the name of someone else
            And I am authenticated as an admin user
            Then the actor and owner will be that someone else
            And the creator will be the admin user
        """
        from .mockers import user_status as activity
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(test_manager), status=201)
        self.assertEqual(res.json['actor']['username'], username)
        self.assertEqual(res.json['creator'], test_manager)
        self.assertEqual(res.json['owner'], username)

    def test_create_activity_as_context_check_ownership(self):
        """
            Given a admin user
            When I post an activity in the name of a context
            And I am authenticated as an admin user
            Then the actor will be that context
            And the creator and owner will be the admin user
        """
        from .mockers import user_status_context
        from .mockers import create_context
        from hashlib import sha1
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.post('/contexts/%s/activities' % url_hash, json.dumps(user_status_context), oauth2Header(test_manager), status=201)
        self.assertEqual(res.json['actor']['hash'], url_hash)
        self.assertEqual(res.json['creator'], test_manager)
        self.assertEqual(res.json['owner'], test_manager)

    def test_create_activity_default_fields(self):
        """
            Given a plain user
            When I create an activity
            Then non-required fields with defaults are set
        """
        from .mockers import user_status as activity
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)
        self.assertIn('replies', res.json)
        self.assertIn('generator', res.json)
        self.assertIn('objectType', res.json)
        self.assertEqual(res.json['objectType'], 'activity')

    def test_post_activity_without_context(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        res = self.create_activity(username, user_status)
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None), None)

    def test_post_activity_with_unauthorized_context(self):
        from .mockers import create_contextA
        from .mockers import user_status_contextA
        username = 'messi'
        self.create_user(username)
        self.create_context(create_contextA)
        res = self.create_activity(username, user_status_contextA, expect=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_post_activity_not_me(self):
        from .mockers import user_status
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username_not_me, user_status, oauth_username=username, expect=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_post_activity_non_existent_user(self):
        from .mockers import user_status
        username = 'messi'
        res = self.create_activity(username, user_status, expect=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'UnknownUserError')

    def test_post_activity_no_auth_headers(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(user_status), status=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_get_activity(self):
        """ doctest .. http:get:: /people/{username}/activities """
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        self.create_activity(username, user_status)
        res = self.testapp.get('/people/%s/activities' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 1)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[0].get('object', None).get('objectType', None), 'note')

    def test_get_activity_not_me(self):
        from .mockers import user_status
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_activity(username_not_me, user_status)
        res = self.testapp.get('/people/%s/activities' % username_not_me, "", oauth2Header(username), status=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_get_activities(self):
        from .mockers import context_query
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username_not_me, user_status_context)
        res = self.testapp.get('/contexts/%s/activities' % (context_query['context']), '', oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertIn('context', result)
        self.assertEqual(result.get('totalItems', None), 2)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result.get('items', None)[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[0].get('contexts', None)[0]['url'], subscribe_context['object']['url'])
        self.assertEqual(result.get('items', None)[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[1].get('contexts', None)[0]['url'], subscribe_context['object']['url'])

    def test_get_activities_does_not_show_private_fields(self):
        """
            Given a plain user
            When I search for activities of a context
            Then i don't have to see any private fields
        """
        from .mockers import context_query
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)
        res = self.testapp.get('/contexts/%s/activities' % (context_query['context']), '', oauth2Header(username), status=200)
        self.assertEqual(res.json.get('totalItems', None), 1)
        self.assertNotIn('_keywords', res.json['items'][0]['object'])

    def test_get_activities_from_inexistent_context(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.get('/activities', {'context': '01234567890abcdef01234567890abcdef012345'}, oauth2Header(username), status=404)

    def test_get_activities_order_sorted_by_last_comment_publish_date(self):
        """
            Given a plain user
            When I post activities on a context
            and I comment on an old activity
            Then the in the comment-sorted activities, the commented activity becomes the first
        """
        from .mockers import user_comment
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        from .mockers import context_query

        from time import sleep
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_0_id = self.create_activity(username, user_status_context).json['id']
        sleep(1)
        activity_1_id = self.create_activity(username, user_status_context).json['id']
        sleep(1)
        activity_2_id = self.create_activity(username, user_status_context).json['id']
        sleep(1)
        res = self.testapp.post('/activities/%s/comments' % str(activity_1_id), json.dumps(user_comment), oauth2Header(username), status=201)

        res = self.testapp.get('/contexts/%s/activities?sortBy=activities' % (context_query['context']), '', oauth2Header(username), status=200)
        self.assertEqual(res.json.get('totalItems', None), 3)
        self.assertEqual(res.json.get('items', None)[0].get('id', None), activity_2_id)
        self.assertEqual(res.json.get('items', None)[1].get('id', None), activity_1_id)
        self.assertEqual(res.json.get('items', None)[2].get('id', None), activity_0_id)

    def test_get_activities_from_recursive_contexts(self):
        """
            Create 3 contexts, one parent and two childs
            The parent context is public-readable, the two childs require subscription
            Create 2 users, messi subscribed to contextA and xavi to both A and B
            Messi querying all activities from parent context, should only get the activity created in contextA
            Xavi querying all activities from parent context, should get the activities from both contexts
        """
        from .mockers import context_query
        from .mockers import create_context
        from .mockers import subscribe_contextA, create_contextA, user_status_contextA
        from .mockers import subscribe_contextB, create_contextB, user_status_contextB
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextA, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextB, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_contextA)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextA)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextB)
        self.create_activity(username, user_status_contextA)
        self.create_activity(username_not_me, user_status_contextA)
        self.create_activity(username_not_me, user_status_contextB)

        res = self.testapp.get('/contexts/%s/activities' % (context_query['context']), '', oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 2)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result.get('items', None)[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[0].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])
        self.assertEqual(result.get('items', None)[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[1].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

        res = self.testapp.get('/contexts/%s/activities' % (context_query['context']), '', oauth2Header(username_not_me), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 3)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result.get('items', None)[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[0].get('contexts', None)[0]['url'], subscribe_contextB['object']['url'])
        self.assertEqual(result.get('items', None)[1].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result.get('items', None)[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[1].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])
        self.assertEqual(result.get('items', None)[2].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[2].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[2].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

    def test_post_activity_with_generator(self):
        """ Post an activity to a context which allows everyone to read and write
        """
        from .mockers import subscribe_context, create_context
        from .mockers import user_status_context_generator
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context_generator)

        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], subscribe_context['object']['url'])
        self.assertEqual(result.get('generator', None), user_status_context_generator['generator'])

    def test_get_timeline(self):
        """ doctest .. http:get:: /people/{username}/timeline """
        from .mockers import user_status, user_status_context, user_status_contextA
        from .mockers import subscribe_context, subscribe_contextA
        from .mockers import create_context, create_contextA
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.create_context(create_contextA)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username, subscribe_contextA)
        self.create_activity(username, user_status)
        self.create_activity(username, user_status_context)
        self.create_activity(username, user_status_contextA)
        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 3)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[0].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])
        self.assertEqual(result.get('items', None)[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[1].get('contexts', None)[0]['url'], subscribe_context['object']['url'])

    def test_get_timeline_does_not_show_private_fields(self):
        """
            Given a plain user
            When I search for activities in timeline
            Then i don't have to see any private fields
        """
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        self.create_activity(username, user_status)
        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        self.assertEqual(res.json.get('totalItems', None), 1)
        self.assertNotIn('_keywords', res.json['items'][0]['object'])

    def test_post_comment(self):
        """ doctest .. http:post:: /activities/{activity}/comments """
        from .mockers import user_status, user_comment
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity = self.create_activity(username, user_status)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)
        result = res.json
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'comment')
        self.assertEqual(result.get('object', None).get('inReplyTo', None)[0].get('id'), str(activity.get('id')))

    def test_get_comments(self):
        """ doctest .. http:get:: /activities/{activity}/comments """
        from .mockers import user_status, user_comment
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity = self.create_activity(username, user_status)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)
        res = self.testapp.get('/activities/%s/comments' % str(activity.get('id')), "", oauth2Header(username), status=200)
        result = res.json
        self.assertEqual(result.get('totalItems', None), 1)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[0].get('objectType', None), 'comment')

    def test_timeline_order_sorted_by_last_comment_publish_date(self):
        """
            Given a plain user
            When I post activities
            and I comment on an old activity
            Then the in the comment-sorted timeline, the commented activity becomes the first
        """
        from .mockers import user_status, user_comment
        from time import sleep
        username = 'messi'
        self.create_user(username)
        activity_0_id = self.create_activity(username, user_status).json['id']
        sleep(1)
        activity_1_id = self.create_activity(username, user_status).json['id']
        sleep(1)
        activity_2_id = self.create_activity(username, user_status).json['id']
        sleep(1)
        res = self.testapp.post('/activities/%s/comments' % str(activity_1_id), json.dumps(user_comment), oauth2Header(username), status=201)

        res = self.testapp.get('/people/%s/timeline?sortBy=comments' % username, "", oauth2Header(username), status=200)
        self.assertEqual(res.json.get('totalItems', None), 3)
        self.assertEqual(res.json.get('items', None)[0].get('id', None), activity_1_id)
        self.assertEqual(res.json.get('items', None)[1].get('id', None), activity_2_id)
        self.assertEqual(res.json.get('items', None)[2].get('id', None), activity_0_id)

    def test_timeline_order_sorted_by_activity_publish_date(self):
        """
            Given a plain user
            When I post activities
            and I comment on an old activity
            Then the in the activities-sorted timeline, the order equals the activity order
        """
        from .mockers import user_status, user_comment
        username = 'messi'
        self.create_user(username)
        activity_0_id = self.create_activity(username, user_status).json['id']
        activity_1_id = self.create_activity(username, user_status).json['id']
        activity_2_id = self.create_activity(username, user_status).json['id']
        res = self.testapp.post('/activities/%s/comments' % str(activity_1_id), json.dumps(user_comment), oauth2Header(username), status=201)

        res = self.testapp.get('/people/%s/timeline?sortBy=activities' % username, "", oauth2Header(username), status=200)
        self.assertEqual(res.json.get('totalItems', None), 3)
        self.assertEqual(res.json.get('items', None)[0].get('id', None), activity_2_id)
        self.assertEqual(res.json.get('items', None)[1].get('id', None), activity_1_id)
        self.assertEqual(res.json.get('items', None)[2].get('id', None), activity_0_id)
