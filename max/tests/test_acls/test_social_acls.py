# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager, test_manager2
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
        pass

    def test_like_contexted_activity(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_like_contexted_activity_no_subscription(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_like_contexted_activity_subscribed_no_read_permission(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_like_uncontexted_activity_impersonating(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_like_contexted_activity_impersonating(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    # Add unlike tests

    def test_unlike_liked_activity(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_unlike_liked_activity_impersonating(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_unlike_non_liked_activity(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    # Add flag tests

    def test_flag_uncontexted_activity(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_flag_contexted_activity(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_flag_contexted_activity_no_subscription(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_flag_contexted_activity_subscribed_no_flag_permission(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_flag_uncontexted_activity_as_manager(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    # Add unflag tests

    def test_unflag_liked_activity(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_unflag_liked_activity_as_manager(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass

    def test_unflag_non_flagged_activity(self):
        """
            Given i'm a regular user
            When I try to like an activity
            Then I succeed
        """
        pass
