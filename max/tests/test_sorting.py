# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header

from copy import deepcopy
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

    def test_get_activities_order_sorted_by_last_comment_publish_date(self):
        """
            Given a plain user
            When I post activities on a context
            and I comment on an old activity
            Then in the comment-sorted activities, the commented activity becomes the first
        """
        from .mockers import user_comment
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        from .mockers import context_query

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_0_id = self.create_activity(username, user_status_context).json['id']
        activity_1_id = self.create_activity(username, user_status_context, note='Second').json['id']
        activity_2_id = self.create_activity(username, user_status_context, note='Third').json['id']
        res = self.testapp.post('/activities/%s/comments' % str(activity_1_id), json.dumps(user_comment), oauth2Header(username), status=201)

        res = self.testapp.get('/contexts/%s/activities?sortBy=activities' % (context_query['context']), '', oauth2Header(username), status=200)
        self.assertEqual(len(res.json), 3)
        self.assertEqual(res.json[0].get('id', None), activity_2_id)
        self.assertEqual(res.json[1].get('id', None), activity_1_id)
        self.assertEqual(res.json[2].get('id', None), activity_0_id)

    def test_timeline_order_sorted_by_last_comment_publish_date(self):
        """
            Given a plain user
            When I post activities
            and I comment on an old activity
            Then in the comment-sorted timeline, the commented activity becomes the first
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

    def test_timeline_order_sorted_by_activity_publish_date(self):
        """
            Given a plain user
            When I post activities
            and I comment on an old activity
            Then in the activities-sorted timeline, the order equals the activity order
        """
        from .mockers import user_status, user_comment
        username = 'messi'
        self.create_user(username)
        activity_0_id = self.create_activity(username, user_status).json['id']
        activity_1_id = self.create_activity(username, user_status, note="second").json['id']
        activity_2_id = self.create_activity(username, user_status, note="third").json['id']
        res = self.testapp.post('/activities/%s/comments' % str(activity_1_id), json.dumps(user_comment), oauth2Header(username), status=201)

        res = self.testapp.get('/people/%s/timeline?sortBy=activities' % username, "", oauth2Header(username), status=200)
        self.assertEqual(len(res.json), 3)
        self.assertEqual(res.json[0].get('id', None), activity_2_id)
        self.assertEqual(res.json[1].get('id', None), activity_1_id)
        self.assertEqual(res.json[2].get('id', None), activity_0_id)
