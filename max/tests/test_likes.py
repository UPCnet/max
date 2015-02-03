# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header

from functools import partial
from mock import patch
from paste.deploy import loadapp

import os
import time
import unittest


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

    def test_likes_sorting_1(self):
        """
            Test without liked objects, sort order must be by descending
            published date of the activities

        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context

        page_size = 3

        # Store the ids of all created activities. First is the oldest
        activities = []
        self.create_context(create_context)

        for i in range(1, 7):
            username = 'user{}'.format(i)
            self.create_user(username)
            self.admin_subscribe_user_to_context(username, subscribe_context)
            res = self.create_activity(username, user_status_context)
            activities.append(res.json['id'])

        firstpage = self.testapp.get('/people/%s/timeline?limit=%d&sortBy=likes' % ("user1", page_size), "", oauth2Header("user1"), status=200)

        self.assertEqual(len(firstpage.json), 3)

        self.assertEqual(firstpage.json[0]['likesCount'], 0)
        self.assertEqual(firstpage.json[0]['id'], activities[5])
        self.assertEqual(firstpage.json[1]['likesCount'], 0)
        self.assertEqual(firstpage.json[1]['id'], activities[4])
        self.assertEqual(firstpage.json[2]['likesCount'], 0)
        self.assertEqual(firstpage.json[2]['id'], activities[3])

        secondpage = self.testapp.get('/people/%s/timeline?sortBy=likes&limit=%d&before=%s' % ("user1", page_size, activities[3]), "", oauth2Header("user1"), status=200)

        self.assertEqual(len(secondpage.json), 3)

        self.assertEqual(secondpage.json[0]['likesCount'], 0)
        self.assertEqual(secondpage.json[0]['id'], activities[2])
        self.assertEqual(secondpage.json[1]['likesCount'], 0)
        self.assertEqual(secondpage.json[1]['id'], activities[1])
        self.assertEqual(secondpage.json[2]['likesCount'], 0)
        self.assertEqual(secondpage.json[2]['id'], activities[0])

    def test_likes_sorting_2(self):
        """
            Test with all activities liked once, sort order must be by descending
            date of the last time that the activity was liked.

        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context

        page_size = 3

        # Store the ids of all created activities. First is the oldest
        activities = []
        self.create_context(create_context)

        # Create 6 users, post an activity with each one and self-like it
        for i in range(1, 7):
            username = 'user{}'.format(i)
            self.create_user(username)
            self.admin_subscribe_user_to_context(username, subscribe_context)
            res = self.create_activity(username, user_status_context)
            activities.append(res.json['id'])

        self.like_activity(username, activities[0])
        self.like_activity(username, activities[3])
        self.like_activity(username, activities[1])
        self.like_activity(username, activities[5])
        self.like_activity(username, activities[4])
        self.like_activity(username, activities[2])

        firstpage = self.testapp.get('/people/%s/timeline?limit=%d&sortBy=likes' % ("user1", page_size), "", oauth2Header("user1"), status=200)

        self.assertEqual(len(firstpage.json), 3)
        self.assertEqual(firstpage.json[0]['likesCount'], 1)
        self.assertEqual(firstpage.json[0]['id'], activities[2])
        self.assertEqual(firstpage.json[1]['likesCount'], 1)
        self.assertEqual(firstpage.json[1]['id'], activities[4])
        self.assertEqual(firstpage.json[2]['likesCount'], 1)
        self.assertEqual(firstpage.json[2]['id'], activities[5])

        secondpage = self.testapp.get('/people/%s/timeline?sortBy=likes&limit=%d&before=%s' % ("user1", page_size, activities[5]), "", oauth2Header("user1"), status=200)

        self.assertEqual(len(secondpage.json), 3)

        self.assertEqual(secondpage.json[0]['likesCount'], 1)
        self.assertEqual(secondpage.json[0]['id'], activities[1])
        self.assertEqual(secondpage.json[1]['likesCount'], 1)
        self.assertEqual(secondpage.json[1]['id'], activities[3])
        self.assertEqual(secondpage.json[2]['likesCount'], 1)
        self.assertEqual(secondpage.json[2]['id'], activities[0])

    def test_timeline_by_likes_paginated_same_likes_span(self):
        """
            Test likes sorting when activities with the same likes span trough
            more than one page, having pages with activities with targeted likeCount
            in the bottom of page, and other on top
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

        # Like activities so activities with 3 likes spans trough pages 1,2 and 3

        self.like_activity('user1', activities[0])
        self.like_activity('user2', activities[0])
        self.like_activity('user3', activities[0])
        self.like_activity('user4', activities[0])
        self.like_activity('user5', activities[0])

        self.like_activity('user1', activities[1])
        self.like_activity('user2', activities[1])
        self.like_activity('user3', activities[1])
        self.like_activity('user4', activities[1])

        time.sleep(1)
        self.like_activity('user1', activities[2])
        self.like_activity('user2', activities[2])
        self.like_activity('user3', activities[2])

        time.sleep(1)
        self.like_activity('user1', activities[3])
        self.like_activity('user2', activities[3])
        self.like_activity('user3', activities[3])

        time.sleep(1)
        self.like_activity('user1', activities[4])
        self.like_activity('user2', activities[4])
        self.like_activity('user3', activities[4])

        time.sleep(1)
        self.like_activity('user1', activities[5])
        self.like_activity('user2', activities[5])
        self.like_activity('user3', activities[5])

        time.sleep(1)
        self.like_activity('user1', activities[6])
        self.like_activity('user2', activities[6])
        self.like_activity('user3', activities[6])

        self.like_activity('user1', activities[7])
        self.like_activity('user2', activities[7])

        self.like_activity('user1', activities[8])

        firstpage = self.testapp.get('/people/%s/timeline?sortBy=likes&limit=3' % "user1", "", oauth2Header("user1"), status=200)

        self.assertEqual(len(firstpage.json), 3)
        self.assertEqual(firstpage.json[0]['likesCount'], 5)
        self.assertEqual(firstpage.json[0]['id'], activities[0])
        self.assertEqual(firstpage.json[1]['likesCount'], 4)
        self.assertEqual(firstpage.json[1]['id'], activities[1])
        self.assertEqual(firstpage.json[2]['likesCount'], 3)
        self.assertEqual(firstpage.json[2]['id'], activities[6])

        secondpage = self.testapp.get('/people/%s/timeline?sortBy=likes&limit=3&before=%s' % ("user1", activities[6]), "", oauth2Header("user1"), status=200)

        self.assertEqual(len(secondpage.json), 3)
        self.assertEqual(secondpage.json[0]['likesCount'], 3)
        self.assertEqual(secondpage.json[0]['id'], activities[5])
        self.assertEqual(secondpage.json[1]['likesCount'], 3)
        self.assertEqual(secondpage.json[1]['id'], activities[4])
        self.assertEqual(secondpage.json[2]['likesCount'], 3)
        self.assertEqual(secondpage.json[2]['id'], activities[3])

        thirdpage = self.testapp.get('/people/%s/timeline?sortBy=likes&limit=3&before=%s' % ("user1", activities[3]), "", oauth2Header("user1"), status=200)

        self.assertEqual(len(thirdpage.json), 3)
        self.assertEqual(thirdpage.json[0]['likesCount'], 3)
        self.assertEqual(thirdpage.json[0]['id'], activities[2])
        self.assertEqual(thirdpage.json[1]['likesCount'], 2)
        self.assertEqual(thirdpage.json[1]['id'], activities[7])
        self.assertEqual(thirdpage.json[2]['likesCount'], 1)
        self.assertEqual(thirdpage.json[2]['id'], activities[8])

        fourthpage = self.testapp.get('/people/%s/timeline?sortBy=likes&limit=3&before=%s' % ("user1", activities[8]), "", oauth2Header("user1"), status=200)
        self.assertEqual(len(fourthpage.json), 1)
        self.assertEqual(fourthpage.json[0]['likesCount'], 0)
        self.assertEqual(fourthpage.json[0]['id'], activities[9])
