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


class ActivitiesACLTests(unittest.TestCase, MaxTestBase):

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

    # Add comment to activity tests

    def test_comment_activity_as_manager(self):
        """
            Given i'm a regular user
            When i try to post a comment on a contextless activity
            I succeed
        """
        pass

    def test_comment_others_activity_as_user(self):
        """
            Given i'm a regular user
            When i try to post a comment on a contextless activity
            I succeed
        """
        pass

    # Add comment to contexted activity tests

    def test_comment_context_activity_as_manager(self):
        """
            Given i'm a regular user
            When i try to post a comment on a contextless activity
            I succeed
        """
        pass

    def test_comment_others_context_activity_as_user(self):
        """
            Given i'm a regular user
            When i try to post a comment on a contexted activity
            And I have permission to write on the context
            Then i succeed
        """
        pass

    def test_comment_others_context_activity_as_user_no_write(self):
        """
            Given i'm a regular user
            When i try to post a comment on a contexted activity
            And I don't have permission to write on the context
            Then i get a Forbidden Exception
        """
        pass

    # Delete activity comment

