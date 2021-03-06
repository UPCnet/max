# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header

from max.utils.dicts import deepcopy
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

    def test_create_activity_with_published_date(self):
        """ doctest .. http:post:: /people/{username}/activities """
        from .mockers import user_status as activity

        old_activity = deepcopy(activity)
        old_activity['published'] = '2010-01-01T00:01:30.000Z'
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(old_activity), oauth2Header(username), status=201)
        self.assertEqual(res.json['published'], '2010-01-01T00:01:30Z')

    def test_create_activity_with_invalid_json(self):
        """ doctest .. http:post:: /people/{username}/activities """
        from .mockers import user_status as activity
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/people/%s/activities' % username, json.dumps(activity)[:-10], oauth2Header(username), status=400)

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

    def test_get_deletable_mark_for_own_activity(self):
        """
           Given a plain user
           When i post an activity
           Then i have the permission to delete it
        """
        from .mockers import user_status as activity
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)
        res = self.testapp.get('/activities/%s' % res.json['id'], '', oauth2Header(username), status=200)
        self.assertEqual(res.json['deletable'], True)

    def test_get_deletable_mark_for_own_activity_in_context(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           Then i have the permission to delete it
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        res = self.create_activity(username, user_status_context)
        res = self.testapp.get('/activities/%s' % res.json['id'], '', oauth2Header(username), status=200)
        self.assertEqual(res.json['deletable'], True)

    def test_get_deletable_mark_for_others_activity_in_context(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           Then i don't have the permission to delete it
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        res = self.create_activity(username, user_status_context)
        res = self.testapp.get('/activities/%s' % res.json['id'], '', oauth2Header(username_not_me), status=200)
        self.assertEqual(res.json['deletable'], False)

    def test_get_deletable_mark_for_others_activity_in_context_with_deletable_permission(self):
        """
           Given a plain user
           and context where everyone can delete
           When another one posts an activity
           Then i have the permission to delete it
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context_deletable_activities
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context_deletable_activities)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        res = self.create_activity(username, user_status_context)
        res = self.testapp.get('/activities/%s' % res.json['id'], '', oauth2Header(username_not_me), status=200)
        self.assertEqual(res.json['deletable'], True)

    def test_get_deletable_mark_for_others_activity(self):
        """
           Given a plain user
           When another user posts an activity
           Then i don't have the permission to delete it
        """
        from .mockers import user_status as activity
        username = 'messi'
        username2 = 'xavi'
        self.create_user(username)
        self.create_user(username2)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)
        res = self.testapp.get('/activities/%s' % res.json['id'], '', oauth2Header(username2), status=200)
        self.assertEqual(res.json['deletable'], False)

    def test_delete_inexistent_activity(self):
        """
            Given a plain user
            When I try to delete an inexistent activity
            Then I get a notfound error
        """
        username = 'messi'
        self.create_user(username)
        self.testapp.delete('/activities/%s' % '000000000000000000000000', '', oauth2Header(username), status=404)

    def test_delete_activity_invalid_id(self):
        """
            Given a plain user
            When I try to delete an inexistent activity
            Then I get a notfound error
        """
        username = 'messi'
        self.create_user(username)
        self.testapp.delete('/activities/%s' % 'invalidid', '', oauth2Header(username), status=400)

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

    def test_create_activity_check_not_duplicate_activity(self):
        """
            Given a admin user
            When I post an activity in the name of someone else
            And I try to post the same content twice in less than a minute
            Then the activity is posted only once
        """
        from .mockers import user_status as activity
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(test_manager), status=201)
        self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(test_manager), status=200)

    def test_create_activity_on_context_check_duplicate_activity(self):
        """
            Given a admin user
            When I post an activity in the name of someone else on a context
            And I try to post the same content twice on another context in less than a minute
            Then the activity is posted again on the new context
        """
        from .mockers import subscribe_contextA, create_contextA, user_status_contextA
        from .mockers import subscribe_contextB, create_contextB, user_status_contextB
        username = 'messi'
        self.create_user(username)
        self.create_context(create_contextA, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextB, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_contextA)
        self.admin_subscribe_user_to_context(username, subscribe_contextB)
        self.testapp.post('/people/%s/activities' % username, json.dumps(user_status_contextA), oauth2Header(test_manager), status=201)
        self.testapp.post('/people/%s/activities' % username, json.dumps(user_status_contextB), oauth2Header(test_manager), status=201)

    def test_create_activity_as_context_check_not_duplicated_activity(self):
        """
            Given a admin user
            When I post an activity in the name of a context
            And I try to post the same content twice in less than a minute
            Then the activity is posted only once
        """
        from .mockers import user_status_as_context
        from .mockers import create_context
        from hashlib import sha1
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        self.testapp.post('/contexts/%s/activities' % url_hash, json.dumps(user_status_as_context), oauth2Header(test_manager), status=201)
        self.testapp.post('/contexts/%s/activities' % url_hash, json.dumps(user_status_as_context), oauth2Header(test_manager), status=200)

    def test_create_activity_as_context_check_ownership(self):
        """
            Given a admin user
            When I post an activity in the name of a context
            And I am authenticated as an admin user
            Then the actor will be that context
            And the creator and owner will be the admin user
        """
        from .mockers import user_status_as_context
        from .mockers import create_context
        from hashlib import sha1
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.post('/contexts/%s/activities' % url_hash, json.dumps(user_status_as_context), oauth2Header(test_manager), status=201)
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
        self.create_activity(username, user_status_contextA, expect=403)

    def test_post_activity_not_me(self):
        from .mockers import user_status
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_activity(username_not_me, user_status, oauth_username=username, expect=403)

    def test_post_activity_non_existent_user(self):
        from .mockers import user_status
        username = 'messi'
        res = self.create_activity(username, user_status, expect=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'UnknownUserError')

    def test_get_activity(self):
        """ doctest .. http:get:: /people/{username}/activities """
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        self.create_activity(username, user_status)
        res = self.testapp.get('/people/%s/activities' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')

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
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_context['object']['url'])
        self.assertEqual(result[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[1].get('contexts', None)[0]['url'], subscribe_context['object']['url'])

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
        self.assertEqual(len(res.json), 1)
        self.assertNotIn('_keywords', res.json[0]['object'])

    def test_get_activities_from_inexistent_context(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.get('/contexts/%s/activities'.format('01234567890abcdef01234567890abcdef012345'), '', oauth2Header(username), status=404)

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
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])
        self.assertEqual(result[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[1].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

        res = self.testapp.get('/contexts/%s/activities' % (context_query['context']), '', oauth2Header(username_not_me), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextB['object']['url'])
        self.assertEqual(result[1].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[1].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])
        self.assertEqual(result[2].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[2].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[2].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])

    def test_get_activities_from_recursive_public_contexts(self):
        from .mockers import context_query
        from .mockers import create_context
        from .mockers import subscribe_contextA, create_contextA, user_status_contextA
        from .mockers import subscribe_contextB, create_contextB, user_status_contextB
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextA, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextB, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextA)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextB)
        self.create_activity(username_not_me, user_status_contextA)
        self.create_activity(username_not_me, user_status_contextB)

        res = self.testapp.get('/contexts/%s/activities' % (context_query['context']), '', oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 2)

    def test_get_activities_from_recursive_public_contexts_filtered_by_tags(self):
        from .mockers import context_query
        from .mockers import create_context
        from .mockers import subscribe_contextA, create_contextA, user_status_contextA
        from .mockers import subscribe_contextB, create_contextB, user_status_contextB
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextA, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextB, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextA)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextB)
        self.create_activity(username_not_me, user_status_contextA)
        self.create_activity(username_not_me, user_status_contextB)

        res = self.testapp.get('/contexts/%s/activities' % (context_query['context']), {'context_tags': ['Assignatura', '']}, oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)

    def test_get_activities_from_recursive_subscribed_contexts(self):
        from .mockers import context_query
        from .mockers import create_context
        from .mockers import subscribe_contextA, create_contextA, user_status_contextA
        from .mockers import subscribe_contextB, create_contextB, user_status_contextB
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context, permissions=dict(read='subscribed', write='restricted', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextA, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.create_context(create_contextB, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextA)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_contextB)
        self.create_activity(username_not_me, user_status_contextA)
        self.create_activity(username_not_me, user_status_contextB)

        self.testapp.get('/contexts/%s/activities' % (context_query['context']), '', oauth2Header(username), status=403)

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

    def test_get_timeline_no_activities(self):
        """ doctest .. http:get:: /people/{username}/timeline """
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 0)

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
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[0].get('contexts', None)[0]['url'], subscribe_contextA['object']['url'])
        self.assertEqual(result[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result[1].get('contexts', None)[0]['url'], subscribe_context['object']['url'])

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
        self.assertEqual(len(res.json), 1)
        self.assertNotIn('_keywords', res.json[0]['object'])

    def test_get_generated_activities_from_another_user(self):
        """
            Given a plain user
            When i search for the generated activities of another user
            Then i get only the ones posted contextless
            And the ones posted to shared contexts
            And the ones posted on public-readable contexts
            And i don't get any posted on a non-shared context
            And i don't get any posted by other users but the requested
        """
        from .mockers import user_status, user_status_context, user_status_contextA, user_status_contextB
        from .mockers import subscribe_context, subscribe_contextA, subscribe_contextB
        from .mockers import create_context, create_contextA, create_contextB
        username1 = 'sheldon'
        username2 = 'penny'
        username3 = 'leonard'
        context_permissions = {'write': 'subscribed', 'read': 'subscribed'}

        self.create_user(username1)
        self.create_user(username2)
        self.create_user(username3)
        self.create_context(create_context, permissions=context_permissions)
        self.create_context(create_contextA, permissions=context_permissions)
        self.create_context(create_contextB)

        # Shared context betweetn user 1 and 2 and 3
        self.admin_subscribe_user_to_context(username1, subscribe_context)
        self.admin_subscribe_user_to_context(username2, subscribe_context)
        self.admin_subscribe_user_to_context(username3, subscribe_context)

        # Contexts only visible by user 1, but B is read-public
        self.admin_subscribe_user_to_context(username1, subscribe_contextA)
        self.admin_subscribe_user_to_context(username1, subscribe_contextB)

        self.create_activity(username1, user_status)
        self.create_activity(username1, user_status_context)
        self.create_activity(username1, user_status_contextA)
        self.create_activity(username1, user_status_contextB)

        self.create_activity(username3, user_status)
        self.create_activity(username3, user_status_context)

        res = self.testapp.get('/people/%s/activities' % username1, "", oauth2Header(username2), status=200)

        self.assertEqual(res.json[0]['contexts'][0]['url'], create_contextB['url'])
        self.assertEqual(res.json[1]['contexts'][0]['url'], create_context['url'])
        self.assertEqual(res.json[2].get('contexts'), None)
        self.assertEqual(len(res.json), 3)
