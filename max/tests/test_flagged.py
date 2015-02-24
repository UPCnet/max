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

    def test_flag_activity(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           And i give someone permission to flag on this context
           Then user with permission can flag
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        from hashlib import sha1

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        chash = sha1(create_context['url']).hexdigest()

        self.admin_subscribe_user_to_context(username, subscribe_context)

        self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, 'flag'), "", oauth2Header(test_manager), status=201)

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=201)
        activity = self.testapp.get('/activities/%s' % activity_id, '', oauth2Header(username), status=200)

        self.assertIn('flagged', activity.json)

    def test_unflag_activity(self):
        """
           Given a plain user
           and a regular context
           and the user has flag permission on this context
           When i post an activity in a context
           And i flag it
           And i unflag it
           Then the activity has no flagged date
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        from hashlib import sha1

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        chash = sha1(create_context['url']).hexdigest()

        self.admin_subscribe_user_to_context(username, subscribe_context)

        self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, 'flag'), "", oauth2Header(test_manager), status=201)

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=201)
        res = self.testapp.delete('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=204)
        activity = self.testapp.get('/activities/%s' % activity_id, '', oauth2Header(username), status=200)

        self.assertIn('flagged', activity.json)
        self.assertEqual(activity.json['flagged'], None)

    def test_flag_already_flagged_activity(self):
        """
           Given a plain user
           and a regular context
           and the user has flag permission on this context
           When i post an activity in a context
           And i flag it twice
           Then the flagged date doesn't change
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        from hashlib import sha1

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        chash = sha1(create_context['url']).hexdigest()

        self.admin_subscribe_user_to_context(username, subscribe_context)

        self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, 'flag'), "", oauth2Header(test_manager), status=201)

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=201)
        activity = self.testapp.get('/activities/%s' % activity_id, '', oauth2Header(username), status=200)

        # wait a second to force flagged date change
        time.sleep(1)

        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=200)
        activity_reflagged = self.testapp.get('/activities/%s' % activity_id, '', oauth2Header(username), status=200)

        self.assertEqual(activity.json['flagged'], activity_reflagged.json['flagged'])

    def test_cannot_flag_activity(self):
        """
           Given a plain user
           and a regular context
           When i post an activity in a context
           And i don't give someone permission to flag on this context
           Then nobody can flag activities on this context
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)

        self.admin_subscribe_user_to_context(username, subscribe_context)

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=401)

    def test_reflag_activity(self):
        """
           Given a plain user
           and a regular context
           and the user has flag permission on this context
           When i post an activity in a context
           And i flag it
           And i unflagg it
           And then i reflag it
           Then the flagged date changes
        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        from hashlib import sha1

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        chash = sha1(create_context['url']).hexdigest()

        self.admin_subscribe_user_to_context(username, subscribe_context)

        self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, 'flag'), "", oauth2Header(test_manager), status=201)

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=201)
        activity = self.testapp.get('/activities/%s' % activity_id, '', oauth2Header(username), status=200)

        # wait a second to force flagged date change
        time.sleep(1)

        # unflag and reflag
        res = self.testapp.delete('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=204)
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=201)
        activity_reflagged = self.testapp.get('/activities/%s' % activity_id, '', oauth2Header(username), status=200)

        self.assertNotEqual(activity.json['flagged'], activity_reflagged.json['flagged'])

    def test_flagged_sorting_1(self):
        """
            Test without flagged objects, sort order must be by descending
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

        # print '\n'.join([str(a) for a in activities])

        firstpage = self.testapp.get('/people/%s/timeline?limit=%d&sortBy=flagged' % ("user1", page_size), "", oauth2Header("user1"), status=200)

        self.assertEqual(len(firstpage.json), 3)

        self.assertEqual(firstpage.json[0]['likesCount'], 0)
        self.assertEqual(firstpage.json[0]['id'], activities[5])
        self.assertEqual(firstpage.json[1]['likesCount'], 0)
        self.assertEqual(firstpage.json[1]['id'], activities[4])
        self.assertEqual(firstpage.json[2]['likesCount'], 0)
        self.assertEqual(firstpage.json[2]['id'], activities[3])

        secondpage = self.testapp.get('/people/%s/timeline?sortBy=flagged&limit=%d&before=%s' % ("user1", page_size, activities[3]), "", oauth2Header("user1"), status=200)

        self.assertEqual(len(secondpage.json), 3)

        self.assertEqual(secondpage.json[0]['likesCount'], 0)
        self.assertEqual(secondpage.json[0]['id'], activities[2])
        self.assertEqual(secondpage.json[1]['likesCount'], 0)
        self.assertEqual(secondpage.json[1]['id'], activities[1])
        self.assertEqual(secondpage.json[2]['likesCount'], 0)
        self.assertEqual(secondpage.json[2]['id'], activities[0])

    def test_flagged_sorting_2(self):
        """
            Test with all activities flagged, sort order must be by descending
            date of the last time that the activity was flagged.

        """
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        from hashlib import sha1
        page_size = 3

        # Store the ids of all created activities. First is the oldest
        activities = []
        self.create_context(create_context)
        chash = sha1(create_context['url']).hexdigest()

        username = 'messi'
        self.create_user(username)
        self.admin_subscribe_user_to_context(username, subscribe_context)

        self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, 'flag'), "", oauth2Header(test_manager), status=201)

        # Create 6 activity
        for i in range(1, 7):
            res = self.create_activity(username, user_status_context)
            activities.append(res.json['id'])

        self.flag_activity(username, activities[0])
        self.flag_activity(username, activities[3])
        self.flag_activity(username, activities[1])
        self.flag_activity(username, activities[5])
        self.flag_activity(username, activities[4])
        self.flag_activity(username, activities[2])

        firstpage = self.testapp.get('/people/%s/timeline?limit=%d&sortBy=flagged' % (username, page_size), "", oauth2Header(username), status=200)
        self.assertEqual(len(firstpage.json), 3)
        self.assertEqual(firstpage.json[0]['id'], activities[2])
        self.assertEqual(firstpage.json[1]['id'], activities[4])
        self.assertEqual(firstpage.json[2]['id'], activities[5])

        secondpage = self.testapp.get('/people/%s/timeline?sortBy=flagged&limit=%d&before=%s' % (username, page_size, activities[5]), "", oauth2Header(username), status=200)

        self.assertEqual(len(secondpage.json), 3)

        self.assertEqual(secondpage.json[0]['id'], activities[1])
        self.assertEqual(secondpage.json[1]['id'], activities[3])
        self.assertEqual(secondpage.json[2]['id'], activities[0])

        # unflag and reflag activity[1] and retest activity order, activity[1] must have turned
        # first and other activities resorted
        self.unflag_activity(username, activities[1])
        self.flag_activity(username, activities[1])

        firstpage = self.testapp.get('/people/%s/timeline?limit=%d&sortBy=flagged' % (username, page_size), "", oauth2Header(username), status=200)
        self.assertEqual(len(firstpage.json), 3)
        self.assertEqual(firstpage.json[0]['id'], activities[1])
        self.assertEqual(firstpage.json[1]['id'], activities[2])
        self.assertEqual(firstpage.json[2]['id'], activities[4])

        secondpage = self.testapp.get('/people/%s/timeline?sortBy=flagged&limit=%d&before=%s' % (username, page_size, activities[4]), "", oauth2Header(username), status=200)

        self.assertEqual(len(secondpage.json), 3)

        self.assertEqual(secondpage.json[0]['id'], activities[5])
        self.assertEqual(secondpage.json[1]['id'], activities[3])
        self.assertEqual(secondpage.json[2]['id'], activities[0])

