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

    def test_like_activity(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           Then someone else can like this activity
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
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username_not_me), status=201)
        activity = self.testapp.get('/activities/%s' % activity_id, '', oauth2Header(username), status=200)

        self.assertEqual(res.json['object']['likes'][0]['username'], username_not_me)
        self.assertEqual(res.json['object']['liked'], True)
        self.assertEqual(res.json['object']['likesCount'], 1)

        self.assertEqual(activity.json['likes'][0]['username'], username_not_me)
        self.assertEqual(activity.json['liked'], False)
        self.assertEqual(activity.json['likesCount'], 1)

    def test_like_already_liked_activity(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           And someone likes this activity
           Then this someone else can't like twice this activity
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
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username_not_me), status=201)
        res = self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username_not_me), status=200)

        self.assertEqual(res.json['object']['likes'][0]['username'], username_not_me)
        self.assertEqual(res.json['object']['liked'], True)
        self.assertEqual(res.json['object']['likesCount'], 1)

    def test_unlike_activity(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           Then someone else can remove previously like mark from this activity
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
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username_not_me), status=201)
        res = self.testapp.delete('/activities/%s/likes/%s' % (activity_id, username_not_me), '', oauth2Header(username_not_me), status=200)
        activity = self.testapp.get('/activities/%s' % activity_id, '', oauth2Header(username), status=200)

        self.assertEqual(res.json['object']['likes'], [])
        self.assertEqual(res.json['object']['liked'], False)
        self.assertEqual(res.json['object']['likesCount'], 0)

        self.assertEqual(activity.json['likes'], [])
        self.assertEqual(activity.json['liked'], False)
        self.assertEqual(activity.json['likesCount'], 0)

    def test_like_activity_by_various(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           Then someone else can like this activity
           and i also can like it
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
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username_not_me), status=201)
        res = self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username), status=201)

        self.assertEqual(res.json['object']['likes'][0]['username'], username_not_me)
        self.assertEqual(res.json['object']['likes'][1]['username'], username)
        self.assertEqual(res.json['object']['liked'], True)
        self.assertEqual(res.json['object']['likesCount'], 2)

    def test_unlike_activity_get_other_likes(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           And varius users like it
           And someone unlike it
           Then someone who unlike this activity
           and the rest of likes remains
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
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username_not_me), status=201)
        res = self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username), status=201)
        res = self.testapp.delete('/activities/%s/likes/%s' % (activity_id, username_not_me), '', oauth2Header(username_not_me), status=200)

        self.assertEqual(res.json['object']['likes'][0]['username'], username)
        self.assertEqual(res.json['object']['liked'], False)
        self.assertEqual(res.json['object']['likesCount'], 1)

    def test_timeline_by_likes(self):
        """
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context

        # Store the ids of all created activities. First is the oldest
        activities = []
        self.create_context(create_context)

        # Create 10 users, subscribe to a context and write a post for each one
        # Like the activities created until then
        # At the and, activity from user 1 will have likes from the rest,
        # and activity by user 10 won't have any likes
        for i in range(1, 11):
            username = 'username{}'.format(i)
            self.create_user(username)
            self.admin_subscribe_user_to_context(username, subscribe_context)
            res = self.create_activity(username, user_status_context)
            for activity_id in activities:
                self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username), status=201)
            activities.append(res.json['id'])

        res = self.testapp.get('/people/%s/timeline?sortBy=likes' % "username1", "", oauth2Header("username1"), status=200)

        self.assertEqual(res.json[0]['likesCount'], 9)
        self.assertEqual(res.json[0]['id'], activities[0])

        self.assertEqual(len(res.json), 9)

    def test_timeline_by_likes_paginated(self):
        """
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context

        # Store the ids of all created activities. First is the oldest
        activities = []
        self.create_context(create_context)

        # Create 10 users, subscribe to a context and write a post for each one
        for i in range(1, 11):
            username = 'user{}'.format(i)
            self.create_user(username)
            self.admin_subscribe_user_to_context(username, subscribe_context)
            res = self.create_activity(username, user_status_context)
            activities.append(res.json['id'])

        # Take the first 6 activities, and make users like it, starting with 6 likes
        # At the end, activity #0 must have 6 likes and activity #5 1 like, decrementing in between

        self.like_activity('user1', activities[0])
        self.like_activity('user2', activities[0])
        self.like_activity('user3', activities[0])
        self.like_activity('user4', activities[0])
        self.like_activity('user5', activities[0])
        self.like_activity('user6', activities[0])

        self.like_activity('user1', activities[1])
        self.like_activity('user2', activities[1])
        self.like_activity('user3', activities[1])
        self.like_activity('user4', activities[1])
        self.like_activity('user5', activities[1])

        self.like_activity('user1', activities[2])
        self.like_activity('user2', activities[2])
        self.like_activity('user3', activities[2])
        self.like_activity('user4', activities[2])

        self.like_activity('user1', activities[3])
        self.like_activity('user2', activities[3])
        self.like_activity('user3', activities[3])

        self.like_activity('user1', activities[4])
        self.like_activity('user2', activities[4])

        self.like_activity('user1', activities[5])

        firstpage = self.testapp.get('/people/%s/timeline?sortBy=likes&limit=3' % "user1", "", oauth2Header("user1"), status=200)

        self.assertEqual(firstpage.json[0]['likesCount'], 6)
        self.assertEqual(firstpage.json[0]['id'], activities[0])
        self.assertEqual(firstpage.json[1]['likesCount'], 5)
        self.assertEqual(firstpage.json[1]['id'], activities[1])
        self.assertEqual(firstpage.json[2]['likesCount'], 4)
        self.assertEqual(firstpage.json[2]['id'], activities[2])

        secondpage = self.testapp.get('/people/%s/timeline?sortBy=likes&limit=3&before=%s' % ("user1", activities[2]), "", oauth2Header("user1"), status=200)

        self.assertEqual(secondpage.json[0]['likesCount'], 3)
        self.assertEqual(secondpage.json[0]['id'], activities[3])
        self.assertEqual(secondpage.json[1]['likesCount'], 2)
        self.assertEqual(secondpage.json[1]['id'], activities[4])
        self.assertEqual(secondpage.json[2]['likesCount'], 1)
        self.assertEqual(secondpage.json[2]['id'], activities[5])

        thirdpage = self.testapp.get('/people/%s/timeline?sortBy=likes&limit=3&before=%s' % ("user1", activities[5]), "", oauth2Header("user1"), status=200)

        self.assertEqual(thirdpage.json[0]['likesCount'], 0)
        self.assertEqual(thirdpage.json[0]['id'], activities[6])
        self.assertEqual(thirdpage.json[1]['likesCount'], 0)
        self.assertEqual(thirdpage.json[1]['id'], activities[7])
        self.assertEqual(thirdpage.json[2]['likesCount'], 0)
        self.assertEqual(thirdpage.json[2]['id'], activities[8])

