# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager, test_manager2
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header
from max.tests.base import impersonate_payload
from functools import partial
from mock import patch
from paste.deploy import loadapp

import json
import os
import unittest


class ConversationsACLTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(os.path.dirname(__file__))

        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('messages')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)

    # Add like tests

    def test_like_uncontexted_activity(self):
        """
            Given i'm a regular user
            When I try to like an uncontexted activity
            Then I succeed
        """
        from max.tests.mockers import user_status

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username_not_me), status=201)

    def test_like_contexted_activity(self):
        """
            Given i'm a regular user
            And i'm subscribed to the activity contexted
            And i have read permission on the context
            When I try to like a contexted activity
            Then I succeed
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context
        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        res = self.create_activity(username, user_status_context)

        activity_id = res.json['id']
        self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username), status=201)

    def test_like_contexted_activity_no_subscription(self):
        """
            Given i'm a regular user
            And i'm not subscribed to the activity context
            When I try to like the contexted activity
            Then I get a Forbidden Exception
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context
        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context, permissions={'read': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)

        activity_id = res.json['id']
        self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username_not_me), status=403)

    def test_like_contexted_activity_subscribed_no_read_permission(self):
        """
            Given i'm a regular user
            And i'm subscribed to the activity context
            And i don't have read permission on the context
            When I try to like the contexted activity
            Then I get a Forbidden Exception
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context
        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context, permissions={'read': 'restricted'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)

        activity_id = res.json['id']
        self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username_not_me), status=403)

    def test_like_uncontexted_activity_impersonating(self):
        """
            Given i'm a Manager user
            When I try to like an activity impersonating as another user
            Then I succeed
        """
        from max.tests.mockers import user_status

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.post('/activities/%s/likes' % activity_id, json.dumps(impersonate_payload({}, username)), oauth2Header(test_manager), status=201)

    def test_like_uncontexted_activity_impersonating_no_privileges(self):
        """
            Given i'm a regular user
            When I try to like an activity impersonating as another user
            Then I get a Forbidden Exception
        """
        from max.tests.mockers import user_status

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.post('/activities/%s/likes' % activity_id, json.dumps(impersonate_payload({}, username)), oauth2Header(username_not_me), status=403)

    # Add unlike tests

    def test_unlike_liked_activity(self):
        """
            Given i'm a regular user
            When I try to unlike an activity
            Then I succeed
        """
        from max.tests.mockers import user_status

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username), status=201)
        self.testapp.delete('/activities/%s/likes/%s' % (activity_id, username), '', oauth2Header(username), status=204)

    def test_unlike_liked_activity_impersonating(self):
        """
            Given i'm a Manager user
            When I try to unlike an activity as someone else
            Then I succeed
        """
        from max.tests.mockers import user_status

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username), status=201)
        self.testapp.delete('/activities/%s/likes/%s' % (activity_id, username), '', oauth2Header(test_manager), status=204)

    def test_unlike_liked_activity_impersonating_no_privileges(self):
        """
            Given i'm a regular user
            When I try to unlike an activity as someone else
            Then I get a Forbidden Exception
        """
        from max.tests.mockers import user_status

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username), status=201)
        self.testapp.delete('/activities/%s/likes/%s' % (activity_id, username), '', oauth2Header(username_not_me), status=403)

    def test_unlike_non_liked_activity(self):
        """
            Given i'm a regular user
            When I try to unlike an activity
            And the activity is not liked
            Then I get a Forbidden Exception
        """
        from max.tests.mockers import user_status

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        self.testapp.delete('/activities/%s/likes/%s' % (activity_id, username), '', oauth2Header(username), status=403)

    # Add flag tests

    def test_flag_uncontexted_activity(self):
        """
            Given i'm a regular user
            When I try to flag an uncontexted activity
            Then I get a Forbidden Exception
        """
        from max.tests.mockers import user_status

        username = 'sheldon'
        self.create_user(username)

        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=403)

    def test_flag_contexted_activity(self):
        """
            Given i'm a regular user
            And i'm subscribed to the activity context
            And i have the flag permission on the context
            When I try to flag a contexted activity
            Then I succeed
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context
        from hashlib import sha1

        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context)
        chash = sha1(create_context['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.grant_permission(chash, username, 'flag')

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=201)

    def test_flag_contexted_activity_no_subscription(self):
        """
            Given i'm a regular user
            And i'm not subscribed to the activity context
            When I try to flag a contexted activity
            Then I get a Forbidden Exception
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)

        self.admin_subscribe_user_to_context(username, subscribe_context)

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username_not_me), status=403)

    def test_flag_contexted_activity_subscribed_no_flag_permission(self):
        """
            Given i'm a regular user
            And i'm subscribed to the activity context
            And i don't have the flag permission on the context
            When I try to flag a contexted activity
            Then I get a Forbidden Exception
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)

        self.admin_subscribe_user_to_context(username, subscribe_context)

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=403)

    def test_flag_contexted_activity_as_manager(self):
        """
            Given i'm a regular user
            When I try to flag a contexted activity
            Then I succeed
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context

        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context)

        self.admin_subscribe_user_to_context(username, subscribe_context)

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(test_manager), status=201)

    # Add unflag tests

    def test_unflag_flagged_activity(self):
        """
            Given i'm a regular user
            And i'm subscribed to the activity context
            And i have the flag permission on the context
            When I try to unflag a flagged activity
            Then I succeed
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context
        from hashlib import sha1

        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context)
        chash = sha1(create_context['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.grant_permission(chash, username, 'flag')

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=201)
        res = self.testapp.delete('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=204)

    def test_unflag_flagged_activity_no_subscription(self):
        """
            Given i'm a regular user
            And i'm not subscribed to the activity context
            When I try to unflag a flagged activity
            Then I get a Forbidden Exception
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context
        from hashlib import sha1

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        chash = sha1(create_context['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.grant_permission(chash, username, 'flag')

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=201)
        res = self.testapp.delete('/activities/%s/flag' % activity_id, '', oauth2Header(username_not_me), status=403)

    def test_unflag_flagged_activity_subscribed_no_flag_permission(self):
        """
            Given i'm a regular user
            And i'm subscribed to the activity context
            And i don't have the flag permission on the context
            When I try to unflag a flagged activity
            Then I get a Forbidden Exception
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context
        from hashlib import sha1

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context)
        chash = sha1(create_context['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        self.grant_permission(chash, username, 'flag')

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=201)
        res = self.testapp.delete('/activities/%s/flag' % activity_id, '', oauth2Header(username_not_me), status=403)

    def test_unflag_flagged_activity_as_manager(self):
        """
            Given i'm a Manager user
            When I try to unflag a flagged activity
            Then I succeed
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context

        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context)

        self.admin_subscribe_user_to_context(username, subscribe_context)

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(test_manager), status=201)
        res = self.testapp.delete('/activities/%s/flag' % activity_id, '', oauth2Header(test_manager), status=204)

    def test_unflag_non_flagged_activity(self):
        """
            Given i'm a regular user
            When I try to unflag a non flagged activity
            Then I succeed
        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context
        from hashlib import sha1

        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context)
        chash = sha1(create_context['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.grant_permission(chash, username, 'flag')

        res = self.create_activity(username, user_status_context)
        activity_id = res.json['id']
        res = self.testapp.delete('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=204)

