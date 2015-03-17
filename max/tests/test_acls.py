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


class ContextACLTests(unittest.TestCase, MaxTestBase):

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

    # Add context tests

    def test_add_context_as_manager(self):
        """
            Given a user that has the Manager role
            When i try to get create a context
            I succeed
        """
        from .mockers import create_context

        self.create_user(test_manager)
        self.testapp.post('/contexts', json.dumps(create_context), oauth2Header(test_manager), status=201)

    def test_add_context_as_non_manager(self):
        """
            Given a user that doesn't have the Manager role
            When i try to create a context
            I get a Forbidden exception
        """
        from .mockers import create_context
        username = 'sheldon'

        self.create_user(username)
        self.testapp.post('/contexts', json.dumps(create_context), oauth2Header(username), status=403)

    # View context tests

    def test_view_context_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to update any context
            I succeed
        """

        from .mockers import create_context
        self.create_user(test_manager)
        res = self.create_context(create_context)
        chash = res.json['hash']
        self.testapp.get('/contexts/%s' % chash, "", oauth2Header(test_manager), status=200)

    def test_view_context_as_non_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to update any context
            I succeed
        """
        from .mockers import create_context
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        res = self.create_context(create_context)
        chash = res.json['hash']
        self.testapp.get('/contexts/%s' % chash, "", oauth2Header(username), status=200)

    # Get all contexts tests

    def test_get_all_contexts_as_manager(self):
        """
            Given a user that has the Manager role
            When i try to get all contexts
            I succeed
        """
        from .mockers import create_context

        self.create_user(test_manager)
        self.create_context(create_context)
        self.testapp.get('/contexts', "", oauth2Header(test_manager), status=200)

    def test_get_all_contexts_as_non_manager(self):
        """
            Given a user that doesn't have the Manager role
            When i try to get all contexts
            I get a Forbidden exception
        """
        from .mockers import create_context
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        self.create_context(create_context)
        self.testapp.get('/contexts', "", oauth2Header(username), status=403)

    # Modify context tests

    def test_modify_context_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to update any context
            I succeed
        """

        from .mockers import create_context
        self.create_user(test_manager)
        res = self.create_context(create_context)
        chash = res.json['hash']
        self.testapp.put('/contexts/%s' % chash, json.dumps({"twitterHashtag": "testhashtag"}), oauth2Header(test_manager), status=200)

    def test_modify_context_as_manager_non_owner(self):
        """
            Given i'm a user that has the Manager role
            And i'm not the owner of the context
            When i try to update any context
            I succeed
        """

        from .mockers import create_context
        self.create_user(test_manager)
        self.create_user(test_manager2)
        res = self.create_context(create_context)
        chash = res.json['hash']
        self.testapp.put('/contexts/%s' % chash, json.dumps({"twitterHashtag": "testhashtag"}), oauth2Header(test_manager2), status=200)

    def test_modify_context_as_owner(self):
        """
            Given i'm a user that don't jave the Manager role
            And is the owner of the context
            When i try to update the context
            I succeed
        """
        from .mockers import create_context
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        res = self.create_context(create_context, owner=username)
        chash = res.json['hash']
        self.testapp.put('/contexts/%s' % chash, json.dumps({"twitterHashtag": "testhashtag"}), oauth2Header(username), status=200)

    def test_modify_context_as_non_owner_non_manager(self):
        """
            Given i'm a user that don't jave the Manager role
            And is the owner of the context
            When i try to update the context
            I succeed
        """
        from .mockers import create_context
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        res = self.create_context(create_context)
        chash = res.json['hash']
        self.testapp.put('/contexts/%s' % chash, json.dumps({"twitterHashtag": "testhashtag"}), oauth2Header(username), status=403)

    # Delete context tests

    def test_delete_context_as_manager(self):
        """
            Given a user that has the Manager role
            When i try to remove a context
            I succeed
        """
        from .mockers import create_context
        self.create_user(test_manager)
        res = self.create_context(create_context)
        chash = res.json['hash']
        self.testapp.delete('/contexts/%s' % (chash,), "", oauth2Header(test_manager), status=204)

    def test_delete_context_as_manager_non_owner(self):
        """
            Given a user that has the Manager role
            And is not the owner of the context
            When i try to remove a context
            I succeed
        """
        from .mockers import create_context
        self.create_user(test_manager)
        self.create_user(test_manager2)
        res = self.create_context(create_context)
        chash = res.json['hash']
        self.testapp.delete('/contexts/%s' % (chash,), "", oauth2Header(test_manager2), status=204)

    def test_delete_context_as_owner(self):
        """
            Given a user that has doesn't have the Manager role
            And is the owner of the context
            When i try to remove a context
            I succeed
        """
        from .mockers import create_context
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        res = self.create_context(create_context, owner=username)
        chash = res.json['hash']
        self.testapp.delete('/contexts/%s' % (chash,), "", oauth2Header(username), status=204)

    def test_delete_context_as_non_manager_neither_owner(self):
        """
            Given a user that has doesn't have the Manager role
            And is not the owner of the context
            When i try to remove a context
            I get a Forbidden
        """
        from .mockers import create_context
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        res = self.create_context(create_context)
        chash = res.json['hash']
        self.testapp.delete('/contexts/%s' % (chash,), "", oauth2Header(username), status=403)
