# -*- coding: utf-8 -*-
import unittest
import os
from paste.deploy import loadapp
import base64
import json

from mock import patch


class mock_post(object):

    def __init__(self, *args, **kwargs):
        pass

    text = ""
    status_code = 200


@patch('requests.post', new=mock_post)
class FunctionalTests(unittest.TestCase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        from webtest import TestApp
        self.testapp = TestApp(self.app)

    def create_user(self, username):
        res = self.testapp.post('/people/%s' % username, "", basicAuthHeader('operations', 'operations'), status=201)
        return res

    def modify_user(self, username, properties):
        res = self.testapp.put('/people/%s' % username, json.dumps(properties), oauth2Header(username))
        return res

    def create_activity(self, username, activity, oauth_username=None, expect=201):
        oauth_username = oauth_username is not None and oauth_username or username
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(oauth_username), status=expect)
        return res

    def create_context(self, context, permissions=None, expect=201):
        default_permissions = dict(read='public', write='public', join='public', invite='subscribed')
        new_context = dict(context)
        if 'permissions' not in new_context:
            new_context['permissions'] = default_permissions
        if permissions:
            new_context['permissions'].update(permissions)
        res = self.testapp.post('/contexts', json.dumps(new_context), basicAuthHeader('operations', 'operations'), status=expect)
        return res

    def modify_context(self, context, properties):
        from hashlib import sha1
        url_hash = sha1(context).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps(properties), basicAuthHeader('operations', 'operations'), status=200)
        return res

    def subscribe_user_to_context(self, username, context, expect=201):
        res = self.testapp.post('/people/%s/subscriptions' % username, json.dumps(context), basicAuthHeader('operations', 'operations'), status=expect)
        return res

    # BEGIN TESTS

    def test_get_all_users(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/admin/people', "", basicAuthHeader('operations', 'operations'))
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 1)
        self.assertEqual(result.get('items', None)[0].get('username'), 'messi')

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
        from .mockers import user_status_contextA
        username = 'messi'
        self.create_user(username)
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
        self.subscribe_user_to_context(username, subscribe_context)
        self.subscribe_user_to_context(username_not_me, subscribe_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username_not_me, user_status_context)
        res = self.testapp.get('/activities', context_query, oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 2)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result.get('items', None)[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[0].get('contexts', None)[0]['object'], subscribe_context['object'])
        self.assertEqual(result.get('items', None)[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[1].get('contexts', None)[0]['object'], subscribe_context['object'])

    def test_get_activities_from_inexistent_context(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.get('/activities', {'context': '01234567890abcdef01234567890abcdef012345'}, oauth2Header(username), status=404)

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
        self.create_context(create_context, permissions=dict(read='public', write='restricted', join='restricted', invite='restricted'))
        self.create_context(create_contextA, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        self.create_context(create_contextB, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        self.subscribe_user_to_context(username, subscribe_contextA)
        self.subscribe_user_to_context(username_not_me, subscribe_contextA)
        self.subscribe_user_to_context(username_not_me, subscribe_contextB)
        self.create_activity(username, user_status_contextA)
        self.create_activity(username_not_me, user_status_contextA)
        self.create_activity(username_not_me, user_status_contextB)

        res = self.testapp.get('/activities', context_query, oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 2)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result.get('items', None)[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[0].get('contexts', None)[0]['object'], subscribe_contextA['object'])
        self.assertEqual(result.get('items', None)[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[1].get('contexts', None)[0]['object'], subscribe_contextA['object'])

        res = self.testapp.get('/activities', context_query, oauth2Header(username_not_me), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 3)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result.get('items', None)[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[0].get('contexts', None)[0]['object'], subscribe_contextB['object'])
        self.assertEqual(result.get('items', None)[1].get('actor', None).get('username'), 'xavi')
        self.assertEqual(result.get('items', None)[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[1].get('contexts', None)[0]['object'], subscribe_contextA['object'])
        self.assertEqual(result.get('items', None)[2].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[2].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[2].get('contexts', None)[0]['object'], subscribe_contextA['object'])

    ## SEARCH ##

    def test_activities_keyword_generation(self):
        """
                Tests that all words passing regex are included in _keywords
                Tests that username that creates the activity is included in keywords
                Tests that a keyword of a comment is included in keywords
        """
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context, user_comment

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', join='restricted', invite='restricted'))
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)
        activity = json.loads(res.text)
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)
        res = self.testapp.get('/activities/%s' % str(activity.get('id')), json.dumps({}), oauth2Header(username), status=200)
        result = json.loads(res.text)
        expected_keywords = [u'comentari', u'messi', u'creaci\xf3', u'testejant', u'canvi', u'una', u'nou', u'activitat']
        self.assertListEqual(result['object']['_keywords'], expected_keywords)

    def test_activities_hashtag_generation(self):
        """
                Tests that all hashtags passing regex are included in _hashtags
                Tests that a hashtag of a comment is included in hashtags
        """
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context_with_hashtag, user_comment_with_hashtag

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', join='restricted', invite='restricted'))
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context_with_hashtag)
        activity = json.loads(res.text)
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment_with_hashtag), oauth2Header(username), status=201)
        res = self.testapp.get('/activities/%s' % str(activity.get('id')), json.dumps({}), oauth2Header(username), status=200)
        result = json.loads(res.text)
        expected_hashtags = [u'canvi', u'comentari', u'nou']
        self.assertListEqual(result['object']['_hashtags'], expected_hashtags)

    def test_context_activities_keyword_search(self):
        """
        """
        from .mockers import context_query_kw_search
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', join='restricted', invite='restricted'))
        self.subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)

        res = self.testapp.get('/activities', context_query_kw_search, oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 1)

    def test_context_activities_author_search(self):
        """
        """
        from .mockers import context_query_author_search
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context

        username = 'messi'
        self.create_user(username)
        username2 = 'xavi'
        self.create_user(username2)
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', join='restricted', invite='restricted'))
        self.subscribe_user_to_context(username, subscribe_context)
        self.subscribe_user_to_context(username2, subscribe_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username2, user_status_context)

        res = self.testapp.get('/activities', context_query_author_search, oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 2)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[1].get('actor', None).get('username'), 'messi')

    def test_subscribe_to_context(self):
        from .mockers import subscribe_context
        from .mockers import user_status_context
        from .mockers import create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['object'], subscribe_context['object'])

    def test_subscribe_to_context_already_subscribed(self):
        from .mockers import subscribe_context
        from .mockers import user_status_context
        from .mockers import create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.subscribe_user_to_context(username, subscribe_context)
        self.subscribe_user_to_context(username, subscribe_context, expect=200)
        res = self.create_activity(username, user_status_context)
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['object'], subscribe_context['object'])

    def test_subscribe_to_inexistent_context(self):
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        res = self.subscribe_user_to_context(username, subscribe_context, expect=404)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'ObjectNotFound')

    def test_get_all_subscribed_contexts_for_user(self):
        from .mockers import create_context
        from .mockers import subscribe_contextA, create_contextA
        from .mockers import subscribe_contextB, create_contextB
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', join='restricted', invite='restricted'))
        self.create_context(create_contextA, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        self.create_context(create_contextB, permissions=dict(read='subscribed', write='subscribed', join='restricted', invite='restricted'))
        self.subscribe_user_to_context(username, subscribe_contextA)
        self.subscribe_user_to_context(username_not_me, subscribe_contextA)
        self.subscribe_user_to_context(username, subscribe_contextB)

        res = self.testapp.get('/people/%s/subscriptions' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 1)
        self.assertEqual(result.get('items', None)[0].get('username', None), 'messi')
        self.assertEqual(result.get('items', None)[0].get('subscribedTo', None).get('totalItems'), 2)
        self.assertEqual(result.get('items', None)[0].get('subscribedTo', None).get('items')[0].get('object').get('url'), 'http://atenea.upc.edu/A')
        self.assertEqual(result.get('items', None)[0].get('subscribedTo', None).get('items')[1].get('object').get('url'), 'http://atenea.upc.edu/B')

    def test_post_activity_with_public_context(self):
        """ Post an activity to a context which allows everyone to read and write
        """
        from .mockers import subscribe_context, create_context
        from .mockers import user_status_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)

        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['object'], subscribe_context['object'])

    def test_post_activity_with_generator(self):
        """ Post an activity to a context which allows everyone to read and write
        """
        from .mockers import subscribe_context, create_context
        from .mockers import user_status_context_generator
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context_generator)

        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['object'], subscribe_context['object'])
        self.assertEqual(result.get('generator', None), user_status_context_generator['generator'])

    def test_post_activity_with_private_read_write_context(self):
        """ Post an activity to a context which needs the user to be subscribed to read and write
            and we have previously subscribed the user.
        """
        from .mockers import subscribe_context, create_context
        from .mockers import user_status_context
        username = 'messi'
        self.create_user(username)
        context_permissions = dict(read='subscribed', write='subscribed', join='restricted', invite='restricted')
        self.create_context(create_context, permissions=context_permissions)
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)

        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['object'], subscribe_context['object'])

    def test_post_activity_with_private_read_context(self):
        """ Try to post an activity to a context which needs the user to be subscribed to read
            but needs to explicitly give write permission on the user to post and we have previously
            subscribed the user but not given write permission.
        """
        from .mockers import subscribe_context, create_context
        from .mockers import user_status_context
        username = 'messi'
        self.create_user(username)
        context_permissions = dict(read='subscribed', write='restricted', join='restricted', invite='restricted')
        self.create_context(create_context, permissions=context_permissions)
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context, expect=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_get_timeline(self):
        from .mockers import user_status, user_status_context, user_status_contextA
        from .mockers import subscribe_context, subscribe_contextA
        from .mockers import create_context, create_contextA
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.create_context(create_contextA)
        self.subscribe_user_to_context(username, subscribe_context)
        self.subscribe_user_to_context(username, subscribe_contextA)
        self.create_activity(username, user_status)
        self.create_activity(username, user_status_context)
        self.create_activity(username, user_status_contextA)
        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 3)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[0].get('contexts', None)[0]['object'], subscribe_contextA['object'])
        self.assertEqual(result.get('items', None)[1].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[1].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[1].get('contexts', None)[0]['object'], subscribe_context['object'])

    def test_post_comment(self):
        from .mockers import user_status, user_comment
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.subscribe_user_to_context(username, subscribe_context)
        activity = self.create_activity(username, user_status)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)
        result = res.json
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'comment')
        self.assertEqual(result.get('object', None).get('inReplyTo', None)[0].get('id'), str(activity.get('id')))

    # ADMIN

    def test_admin_post_activity_without_context(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/admin/people/%s/activities' % username, json.dumps(user_status), basicAuthHeader('admin', 'admin'))
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None), None)

    def test_admin_post_activity_with_context(self):
        from .mockers import subscribe_context
        from .mockers import user_status_context
        from .mockers import create_context

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.testapp.post('/admin/people/%s/activities' % username, json.dumps(user_status_context), basicAuthHeader('admin', 'admin'))
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['object'], subscribe_context['object'])

    def test_admin_post_activity_with_context_as_actor(self):
        from .mockers import subscribe_context
        from .mockers import user_status_context
        from .mockers import create_context
        from hashlib import sha1
        self.create_context(create_context)
        url_hash = sha1(create_context['object']['url']).hexdigest()
        res = self.testapp.post('/admin/contexts/%s/activities' % url_hash, json.dumps(user_status_context), basicAuthHeader('admin', 'admin'))
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('hash', None), url_hash)
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['object'], subscribe_context['object'])

    # def test_admin_post_activity_with_unauthorized_context_type_as_actor(self):
    #     from .mockers import create_unauthorized_context
    #     from hashlib import sha1

    #     result = self.create_context(create_invalid_context, expect=201)
    #     import ipdb;ipdb.set_trace()
        # url_hash = sha1(create_invalid_context['object']['url']).hexdigest()
        # res = self.testapp.post('/admin/contexts/%s/activities' % url_hash, json.dumps(user_status_context), basicAuthHeader('admin', 'admin'))
        # result = json.loads(res.text)
        # self.assertEqual(result.get('actor', None).get('hash', None), url_hash)
        # self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        # self.assertEqual(result.get('contexts', None)[0], subscribe_context['object'])
    # CONTEXTS

    def test_add_public_context(self):
        from hashlib import sha1
        from .mockers import create_context
        res = self.testapp.post('/contexts', json.dumps(create_context), basicAuthHeader('operations', 'operations'), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.assertEqual(result.get('hash', None), url_hash)

    def test_add_invalid_context(self):
        from .mockers import create_invalid_context
        self.create_context(create_invalid_context, expect=400)

    def test_add_uri_context_without_displayName(self):
        """
            Add a Uri context without a displayName and check that the default displayName is set
            with the url from the uri object
        """
        from .mockers import create_context_without_displayname
        res = self.create_context(create_context_without_displayname, expect=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('displayName', None), create_context_without_displayname['object']['url'])

    # CONTEXTS

    def test_add_public_context_with_all_params(self):
        from hashlib import sha1
        from .mockers import create_context_full
        res = self.testapp.post('/contexts', json.dumps(create_context_full), basicAuthHeader('operations', 'operations'), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context_full['object']['url']).hexdigest()
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('displayName', None), create_context_full['displayName'])
        self.assertEqual(result.get('twitterHashtag', None), create_context_full['twitterHashtag'])
        self.assertEqual(result.get('twitterUsername', None), create_context_full['twitterUsername'])

    def test_context_exists(self):
        from hashlib import sha1
        from .mockers import create_context
        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.create_context(create_context)
        res = self.testapp.get('/contexts/%s' % url_hash, "", basicAuthHeader('operations', 'operations'), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)

    def test_modify_context(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1"}), basicAuthHeader('operations', 'operations'), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('twitterHashtag', None), 'assignatura1')

    def test_modify_context_with_twitter_username(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1", "twitterUsername": "maxupcnet"}), basicAuthHeader('operations', 'operations'), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('twitterHashtag', None), 'assignatura1')
        self.assertEqual(result.get('twitterUsername', None), 'maxupcnet')
        self.assertEqual(result.get('twitterUsernameId', None), '526326641')

    def test_modify_context_unsetting_property(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.modify_context(create_context['object']['url'], {"twitterHashtag": "assignatura1", "twitterUsername": "maxupcnet"})
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura4", "twitterUsername": ""}), basicAuthHeader('operations', 'operations'), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('twitterHashtag', None), 'assignatura4')
        self.assertEqual(result.get('twitterUsername', None), None)
        self.assertEqual(result.get('twitterUsernameId', None), None)

    def test_delete_context(self):
        from hashlib import sha1
        from .mockers import create_context
        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.create_context(create_context)
        self.testapp.delete('/contexts/%s' % url_hash, "", basicAuthHeader('operations', 'operations'), status=204)

    def test_deleted_context_is_really_deleted(self):
        from hashlib import sha1
        from .mockers import create_context
        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.create_context(create_context)
        self.testapp.delete('/contexts/%s' % url_hash, "", basicAuthHeader('operations', 'operations'), status=204)
        res = self.testapp.get('/contexts/%s' % url_hash, "", basicAuthHeader('operations', 'operations'), status=404)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'ObjectNotFound')

    def test_delete_only_deleted_specified_context(self):
        from hashlib import sha1
        from .mockers import create_context, create_contextA
        self.create_context(create_context)
        self.create_context(create_contextA)

        url_hash = sha1(create_context['object']['url']).hexdigest()
        url_hashA = sha1(create_contextA['object']['url']).hexdigest()
        self.testapp.delete('/contexts/%s' % url_hash, "", basicAuthHeader('operations', 'operations'), status=204)
        res = self.testapp.get('/contexts/%s' % url_hashA, "", basicAuthHeader('operations', 'operations'), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hashA)

    # def test_delete_context_removes_subscription_from_user(self):
    #     """
    #     """
    #     from hashlib import sha1
    #     from .mockers import subscribe_context, create_context
    #     from .mockers import user_status_context
    #     username = 'messi'
    #     self.create_user(username)
    #     self.create_context(create_context)
    #     self.subscribe_user_to_context(username, subscribe_context)
    #     self.create_activity(username, user_status_context)

    #     url_hash = sha1(create_context['object']['url']).hexdigest()
    #     self.testapp.delete('/contexts/%s' % url_hash, "", basicAuthHeader('operations', 'operations'), status=204)

    #     res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
    #     result = json.loads(res.text)

    #     self.assertEqual(result.get('username', None), 'messi')
    #     self.assertEqual(result.get('subscribedTo', {}).get('totalItems', None), 0)

    def test_add_private_rw_context(self):
        from hashlib import sha1
        from .mockers import create_context_private_rw
        res = self.testapp.post('/contexts', json.dumps(create_context_private_rw), basicAuthHeader('operations', 'operations'), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context_private_rw['object']['url']).hexdigest()
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('permissions', None), create_context_private_rw['permissions'])

    def test_add_private_r_context(self):
        from hashlib import sha1
        from .mockers import create_context_private_r
        res = self.testapp.post('/contexts', json.dumps(create_context_private_r), basicAuthHeader('operations', 'operations'), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context_private_r['object']['url']).hexdigest()
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('permissions', None), create_context_private_r['permissions'])

    def test_check_permissions_on_subscribed_rw_context(self):
        from .mockers import create_context_private_rw, subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_rw)
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('subscribedTo', {}).get('totalItems'), 1)
        self.assertEqual(result.get('subscribedTo', {}).get('items')[0]['object']['url'], subscribe_context['object']['url'])
        self.assertEqual('read' in result.get('subscribedTo', {}).get('items')[0]['permissions'], True)
        self.assertEqual('write' in result.get('subscribedTo', {}).get('items')[0]['permissions'], True)

    def test_check_permissions_on_subscribed_write_restricted_context(self):
        from .mockers import create_context_private_r, subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('subscribedTo', {}).get('totalItems'), 1)
        self.assertEqual(result.get('subscribedTo', {}).get('items')[0]['object']['url'], subscribe_context['object']['url'])
        self.assertEqual('read' in result.get('subscribedTo', {}).get('items')[0]['permissions'], True)
        self.assertEqual('write' not in result.get('subscribedTo', {}).get('items')[0]['permissions'], True)

    def test_post_on_subscribed_write_restricted_context_without_write_permission(self):
        from .mockers import create_context_private_r, subscribe_context, user_status_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context, expect=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_post_on_subscribed_rw_context(self):
        from .mockers import create_context_private_rw, subscribe_context, user_status_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_rw)
        self.subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['object']['url'], user_status_context['contexts'][0]['url'])

    def test_grant_write_permission_on_write_restricted_context(self):
        from .mockers import create_context_private_r, subscribe_context
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.subscribe_user_to_context(username, subscribe_context)
        chash = sha1(create_context_private_r['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s/permissions/%s/write' % (chash, username), "", basicAuthHeader('operations', 'operations'), status=201)
        result = json.loads(res.text)
        self.assertEqual('read' in result['permissions'], True)
        self.assertEqual('write' in result['permissions'], True)

    def test_revoke_write_permission_on_write_restricted_context(self):
        from .mockers import create_context_private_r, subscribe_context
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.subscribe_user_to_context(username, subscribe_context)
        chash = sha1(create_context_private_r['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s/permissions/%s/write' % (chash, username), "", basicAuthHeader('operations', 'operations'), status=201)
        res = self.testapp.delete('/contexts/%s/permissions/%s/write' % (chash, username), "", basicAuthHeader('operations', 'operations'), status=200)
        result = json.loads(res.text)
        self.assertEqual('read' in result['permissions'], True)
        self.assertEqual('write' not in result['permissions'], True)

    def test_grant_write_permission_on_non_subscribed_context(self):
        from .mockers import create_context_private_r
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        chash = sha1(create_context_private_r['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s/permissions/%s/write' % (chash, username), "", basicAuthHeader('operations', 'operations'), status=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_grant_invalid_permission_on_subscribed_context(self):
        from .mockers import create_context_private_r, subscribe_context
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.subscribe_user_to_context(username, subscribe_context)
        chash = sha1(create_context_private_r['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s/permissions/%s/badpermission' % (chash, username), "", basicAuthHeader('operations', 'operations'), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'InvalidPermission')


def basicAuthHeader(username, password):
    base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
    return dict(Authorization="Basic %s" % base64string)


def oauth2Header(username):
    return {"X-Oauth-Token": "jfa1sDF2SDF234", "X-Oauth-Username": username, "X-Oauth-Scope": "widgetcli"}
