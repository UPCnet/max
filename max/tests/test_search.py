# -*- coding: utf-8 -*-
import os
import json
import unittest
from functools import partial

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header, mock_post
from max.tests import test_manager, test_default_security


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

    # BEGIN TESTS

    def test_activities_keyword_generation(self):
        """
                Tests that all words passing regex are included in keywords
                Tests that username that creates the activity is included in keywords
                Tests that displayName of user that creates the activity is included in keywords
                Tests that username that creates the comment is included in keywords
                Tests that displayName of user that creates the comment is included in keywords
                Tests that a keyword of a comment is included in keywords
        """
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context, user_comment

        username = 'messi'
        username2 = 'xavi'
        self.create_user(username, displayName="Lionel Messi")
        self.create_user(username2, displayName="Xavi Hernandez")
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity = self.create_activity(username, user_status_context).json
        res = self.testapp.post('/activities/%s/comments' % str(activity['id']), json.dumps(user_comment), oauth2Header(username2), status=201)
        res = self.testapp.get('/activities/%s' % str(activity['id']), json.dumps({}), oauth2Header(username), status=200)
        expected_keywords = [u'activitat', u'canvi', u'comentari', u'creaci\xf3', u'estatus', u'hernandez', u'lionel', u'messi', u'nou', u'testejant', u'una', u'xavi']
        response_keywords = res.json['keywords']
        response_keywords.sort()
        self.assertListEqual(response_keywords, expected_keywords)

    def test_activities_keyword_generation_after_comment_delete(self):
        """
            test that the keywords supplied by a comment disappers from activity when deleting the comment
        """
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context, user_comment

        username = 'messi'
        username2 = 'xavi'
        self.create_user(username, displayName="Lionel Messi")
        self.create_user(username2, displayName="Xavi Hernandez")
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity = self.create_activity(username, user_status_context).json
        res = self.testapp.post('/activities/%s/comments' % str(activity['id']), json.dumps(user_comment), oauth2Header(username2), status=201)
        comment_id = res.json['id']
        res = self.testapp.delete('/activities/%s/comments/%s' % (str(activity['id']), comment_id), "", oauth2Header(username2), status=204)
        res = self.testapp.get('/activities/%s' % str(activity['id']), json.dumps({}), oauth2Header(username), status=200)
        expected_keywords = [u'canvi', u'creaci\xf3', u'estatus', u'lionel', u'messi', u'testejant']
        response_keywords = res.json['keywords']
        response_keywords.sort()
        self.assertListEqual(response_keywords, expected_keywords)

    def test_activities_hashtag_generation(self):
        """
                Tests that all hashtags passing regex are included in _hashtags
                Tests that a hashtag of a comment is included in hashtags
        """
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context_with_hashtag, user_comment_with_hashtag

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context_with_hashtag)
        activity = json.loads(res.text)
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment_with_hashtag), oauth2Header(username), status=201)
        res = self.testapp.get('/activities/%s' % str(activity.get('id')), json.dumps({}), oauth2Header(username), status=200)
        result = json.loads(res.text)
        expected_hashtags = [u'canvi', u'comentari', u'nou']
        self.assertListEqual(result['object']['hashtags'], expected_hashtags)

    def test_context_activities_keyword_search(self):
        """
        """
        from .mockers import context_query
        from .mockers import context_query_kw_search
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)

        res = self.testapp.get('/contexts/%s/activities' % (context_query['context']), context_query_kw_search, oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)

    def test_context_activities_actor_search(self):
        """
        """
        from .mockers import context_query
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context

        username = 'messi'
        self.create_user(username)
        username2 = 'xavi'
        self.create_user(username2)
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username2, subscribe_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username2, user_status_context)

        res = self.testapp.get('/contexts/%s/activities?actor=%s' % (context_query['context'], username), '', oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[1].get('actor', None).get('username'), 'messi')

    def test_timeline_activities_actor_search(self):
        """
        """
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context

        username = 'messi'
        self.create_user(username)
        username2 = 'xavi'
        self.create_user(username2)
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username2, subscribe_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username2, user_status_context)
        self.create_activity(username2, user_status_context)

        res = self.testapp.get('/people/%s/timeline?actor=%s' % (username, username), '', oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result[1].get('actor', None).get('username'), 'messi')

    def test_contexts_search(self):
        """
            Given an admin user
            When I search for all contexts
            Then I get them all
        """
        from .mockers import create_context, create_contextA, create_contextB

        self.create_context(create_context)
        self.create_context(create_contextA)
        self.create_context(create_contextB)
        res = self.testapp.get('/contexts', '', oauth2Header(test_manager), status=200)
        self.assertEqual(len(res.json), 3)

    def test_contexts_search_with_tags(self):
        """
            Given an admin user
            When I search for contexts with a tag
            Then I get tthe ones with that tag
        """
        from .mockers import create_context, create_contextA, create_contextB
        from .mockers import context_search_by_tags

        self.create_context(create_context)   # Tagged "Assignatura"
        self.create_context(create_contextA)  # Tagged "Assignatura"
        self.create_context(create_contextB)  # Not tagged
        res = self.testapp.get('/contexts?tags', context_search_by_tags, oauth2Header(test_manager), status=200)
        self.assertEqual(len(res.json), 2)

    def test_public_contexts_search_with_tags(self):
        """
            Given a plain user
            When I search for public contexts with a tag
            Then I get the ones with that tag
        """
        from .mockers import create_context, create_contextA, create_contextB
        from .mockers import context_search_by_tags

        username = 'messi'
        self.create_user(username)

        self.create_context(create_context)
        self.create_context(create_contextA, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='subscribed'))
        self.create_context(create_contextB)
        res = self.testapp.get('/contexts/public?tags', context_search_by_tags, oauth2Header(username), status=200)
        self.assertEqual(len(res.json), 1)

    def test_search_with_invalid_parameters(self):
        """
            Given a plain user
            When I do a search with invalid parameters
            Then I get a Bad Request Error
        """
        username = 'messi'
        self.create_user(username)
        fake_id = '519200000000000000000000'
        self.testapp.get('/people?limit=a', '', oauth2Header(username), status=400)
        self.testapp.get('/people?after=0', '', oauth2Header(username), status=400)
        self.testapp.get('/people?before=0', '', oauth2Header(username), status=400)
        self.testapp.get('/people?before={0}&after={0}'.format(fake_id), '', oauth2Header(username), status=400)

    def test_context_timeline_favorites_search(self):
        """
        """
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context

        username = 'messi'
        self.create_user(username)
        username2 = 'xavi'
        self.create_user(username2)
        self.create_context(create_context, permissions=dict(read='public', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username2, subscribe_context)
        res = self.create_activity(username, user_status_context)
        activity1_id = res.json['id']
        self.create_activity(username, user_status_context)
        res = self.create_activity(username2, user_status_context)
        activity3_id = res.json['id']
        self.create_activity(username2, user_status_context)

        self.favorite_activity(username, activity1_id)
        self.favorite_activity(username, activity3_id)

        res = self.testapp.get('/people/%s/timeline?favorites=true' % (username), '', oauth2Header(username), status=200)
        self.assertEqual(len(res.json), 2)
        self.assertEqual(res.json[0]['id'], activity3_id)
        self.assertEqual(res.json[1]['id'], activity1_id)