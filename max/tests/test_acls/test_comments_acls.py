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
            Given i'm a Manager user
            When i try to post a comment on a contextless activity
            I succeed
        """
        from max.tests.mockers import user_status as activity
        from max.tests.mockers import user_comment as comment
        username = 'sheldon'
        self.create_user(username)
        activity_id = self.create_activity(username, activity).json['id']
        self.comment_activity(test_manager, activity_id, comment, expect=201)

    def test_comment_others_activity_as_user(self):
        """
            Given i'm a regular user
            When i try to post a comment on a contextless activity
            I succeed
        """
        from max.tests.mockers import user_status as activity
        from max.tests.mockers import user_comment as comment
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        activity_id = self.create_activity(username, activity).json['id']
        self.comment_activity(other, activity_id, comment, expect=201)

    def test_comment_others_activity_as_owner(self):
        """
            Given i'm the owner of the activity
            When i try to post a comment on a contextless activity i own
            I succeed
        """
        from max.tests.mockers import user_status as activity
        from max.tests.mockers import user_comment as comment
        username = 'sheldon'
        self.create_user(username)
        activity_id = self.create_activity(username, activity).json['id']
        self.comment_activity(username, activity_id, comment, expect=201)

    # Add comment to contexted activity tests

    def test_comment_context_activity_as_manager(self):
        """
            Given i'm a Manager user
            When i try to post a comment on a contexted activity
            I succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        self.comment_activity(test_manager, activity_id, comment, expect=201)

    def test_comment_onw_context_activity_as_user(self):
        """
            Given i'm a regular user
            When i try to post a comment on a contexted activity that i own
            And I have permission to write on the context
            Then i succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context, permissions={'write': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        self.comment_activity(username, activity_id, comment, expect=201)

    def test_comment_others_context_activity_as_user(self):
        """
            Given i'm a regular user
            When i try to post a comment on a someone else's contexted activity
            And I have permission to write on the context
            Then i succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(other, activity).json['id']
        self.comment_activity(username, activity_id, comment, expect=201)

    def test_comment_others_context_activity_as_context_owner(self):
        """
            Given i'm the owner of a context
            When i try to post a comment on a contexted activity
            And I have permission to write on the context
            Then i succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, owner=username, permissions={'write': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(other, activity).json['id']
        self.comment_activity(username, activity_id, comment, expect=201)

    def test_comment_others_context_activity_as_context_owner_no_write(self):
        """
            Given i'm the owner of a context
            When i try to post a comment on a contexted activity
            And I don't have permission to write on the context
            Then i get a Forbidden Exception
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        self.create_user(username)
        url_hash = self.create_context(create_context, owner=username, permissions={'write': 'subscribed'}).json['hash']
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        self.revoke_permission(url_hash, username, 'write')
        self.comment_activity(username, activity_id, comment, expect=403)

    def test_comment_others_context_activity_as_user_no_write(self):
        """
            Given i'm a regular user
            When i try to post a comment on a contexted activity
            And I don't have permission to write on the context
            Then i get a Forbidden Exception
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        self.create_user(username)
        url_hash = self.create_context(create_context, permissions={'write': 'subscribed'}).json['hash']
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        self.revoke_permission(url_hash, username, 'write')
        self.comment_activity(username, activity_id, comment, expect=403)

    # Delete activity comment tests

    def test_delete_comment_activity_as_manager(self):
        """
            Given i'm a Manager user
            When i try to delete a comment from a contextless activity
            I succeed
        """
        from max.tests.mockers import user_status as activity
        from max.tests.mockers import user_comment as comment
        username = 'sheldon'
        self.create_user(username)
        activity_id = self.create_activity(username, activity).json['id']
        comment_id = self.comment_activity(username, activity_id, comment).json['id']
        self.delete_activity_comment(test_manager, activity_id, comment_id, expect=204)

    def test_delete_comment_activity_as_comment_owner(self):
        """
            Given i'm a regular user
            When i try to delete a comment from a contextless activity
            and im the owner of the comment
            I succeed
        """
        from max.tests.mockers import user_status as activity
        from max.tests.mockers import user_comment as comment
        username = 'sheldon'
        self.create_user(username)
        activity_id = self.create_activity(username, activity).json['id']
        comment_id = self.comment_activity(username, activity_id, comment).json['id']
        self.delete_activity_comment(username, activity_id, comment_id, expect=204)

    def test_delete_others_comment_activity_as_activity_owner(self):
        """
            Given i'm the Owner of an activity
            When i try to delete a comment from a the activivyt
            And i'm not the owner of the comment
            I succeed
        """
        from max.tests.mockers import user_status as activity
        from max.tests.mockers import user_comment as comment
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        activity_id = self.create_activity(username, activity).json['id']
        comment_id = self.comment_activity(other, activity_id, comment).json['id']
        self.delete_activity_comment(username, activity_id, comment_id, expect=204)

    def test_delete_others_comment_activity(self):
        """
            Given i'm a regular user
            When i try to delete a comment from a contextless activity
            and i'm not the owner of the comment
            And i'm not the owner of the activity
            I get a Forbidden exception
        """
        from max.tests.mockers import user_status as activity
        from max.tests.mockers import user_comment as comment
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        activity_id = self.create_activity(other, activity).json['id']
        comment_id = self.comment_activity(other, activity_id, comment).json['id']
        self.delete_activity_comment(username, activity_id, comment_id, expect=403)

    # Delete contexted activity comment tests

    def test_delete_context_comment_activity_as_manager(self):
        """
            Given i'm a Manager user
            When i try to delete a comment from a contexted activity
            I succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context, permissions={'write': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        comment_id = self.comment_activity(username, activity_id, comment).json['id']
        self.delete_activity_comment(test_manager, activity_id, comment_id, expect=204)

    def test_delete_context_comment_activity_as_comment_owner(self):
        """
            Given i'm a regular user
            When i try to delete a comment from a contexted activity
            and im the owner of the comment
            I succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context, owner=username, permissions={'write': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        comment_id = self.comment_activity(username, activity_id, comment).json['id']
        self.delete_activity_comment(username, activity_id, comment_id, expect=204)

    def test_delete_context_others_comment_activity_as_activity_owner(self):
        """
            Given i'm a regular user
            When i try to delete a comment from a contexted activity
            And i'm not the owner of the comment
            And i'm the owner of the activity
            I succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        comment_id = self.comment_activity(other, activity_id, comment).json['id']
        self.delete_activity_comment(username, activity_id, comment_id, expect=204)

    def test_delete_context_others_comment_activity_with_delete_permission(self):
        """
            Given i'm a regular user
            When i try to delete a comment from a contexted activity
            And i'm not the owner of the activity
            And i'm not the owner of the comment
            And i have delete permission on my context subscription
            I succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        chash = self.create_context(create_context, permissions={'write': 'subscribed', 'delete': 'restricted'}).json['hash']
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(other, activity).json['id']
        comment_id = self.comment_activity(other, activity_id, comment).json['id']
        self.grant_permission(chash, username, 'delete')
        self.delete_activity_comment(username, activity_id, comment_id, expect=204)

    def test_delete_context_comment_activity_as_context_owner(self):
        """
            Given i'm a Owner of a context
            When i try to delete a comment from that context
            and i'm not the owner of the activity
            and i'm not the owner of the comment
            and i don't have explicit delete permission
            I get a Forbidden Exception
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, owner=username, permissions={'write': 'subscribed', 'delete': 'restricted'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(other, activity).json['id']
        comment_id = self.comment_activity(other, activity_id, comment).json['id']
        self.delete_activity_comment(username, activity_id, comment_id, expect=403)

    def test_delete_context_others_comment_activity(self):
        """
            Given i'm a regular user
            When i try to delete a comment from a contexted activity
            and i'm not the owner of the activity
            and i'm not the owner of the comment
            I get a Forbidden exception
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import user_comment as comment
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed', 'delete': 'restricted'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(other, activity).json['id']
        comment_id = self.comment_activity(other, activity_id, comment).json['id']
        self.delete_activity_comment(username, activity_id, comment_id, expect=403)

    # Get all user comments tests

    def test_get_all_user_comments(self):
        """
            Given i'm a regular user
            When i try to get all the comments i wrote anywhere
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        self.testapp.get('/people/{}/comments'.format(username), "", headers=oauth2Header(username), status=200)

    def test_get_all_other_user_comments_as_manager(self):
        """
            Given i'm a Manager user
            When i try to get all the comments someone else wrote
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        self.testapp.get('/people/{}/comments'.format(username), "", headers=oauth2Header(test_manager), status=200)

    def test_get_all_other_user_comments(self):
        """
            Given i'm a regular user
            When i try to get all the comments someone else wrote
            I get a Forbidden exception
        """
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.testapp.get('/people/{}/comments'.format(username), "", headers=oauth2Header(other), status=403)

    # Get all activity comments tests

    def test_get_all_activity_comments_as_manager(self):
        """
            Given i'm a Manager user
            When i try to get all the comments posted on a contextless activity
            I succeed
        """
        from max.tests.mockers import user_status as activity
        username = 'sheldon'
        self.create_user(username)
        activity_id = self.create_activity(username, activity).json['id']
        self.testapp.get('/activities/{}/comments'.format(activity_id), "", headers=oauth2Header(test_manager), status=200)

    def test_get_all_activity_comments_as_activity_owner(self):
        """
            Given i'm the Owner of a contextless activity
            When i try to get all the comments posted on the activity
            I succeed
        """
        from max.tests.mockers import user_status as activity
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        activity_id = self.create_activity(username, activity).json['id']
        self.testapp.get('/activities/{}/comments'.format(activity_id), "", headers=oauth2Header(username), status=200)

    def test_get_all_activity_comments(self):
        """
            Given i'm a regular user
            When i try to get all the comments from a contextless activity
            And i don't own that activity
            I succeed
        """
        from max.tests.mockers import user_status as activity
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        activity_id = self.create_activity(username, activity).json['id']
        self.testapp.get('/activities/{}/comments'.format(activity_id), "", headers=oauth2Header(other), status=200)

    # Get all contexted activity comments tests

    def test_get_all_contexted_activity_comments_as_manager(self):
        """
            Given i'm a Manager user
            When i try to get all the comments posted on a contexted activity
            I succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context, permissions={'write': 'subscribed', 'delete': 'restricted'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        self.testapp.get('/activities/{}/comments'.format(activity_id), "", headers=oauth2Header(test_manager), status=200)

    def test_get_all_contexted_activity_comments_as_activity_owner(self):
        """
            Given i'm the Owner of a contextless activity
            When i try to get all the comments posted on the activity
            I succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        self.testapp.get('/activities/{}/comments'.format(activity_id), "", headers=oauth2Header(username), status=200)

    def test_get_all_contexted_activity_comments(self):
        """
            Given i'm a regular user
            When i try to get all the comments from a contexted activity
            And i don't own the activity
            And i'm subscribed to the context
            And i have read permission on the context
            I succeed
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        self.testapp.get('/activities/{}/comments'.format(activity_id), "", headers=oauth2Header(other), status=200)

    def test_get_all_contexted_activity_comments_non_subscribed(self):
        """
            Given i'm a regular user
            When i try to get all the comments from a contexted activity
            And i'm not subscribed to the context
            I get a Forbidden exception
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        self.testapp.get('/activities/{}/comments'.format(activity_id), "", headers=oauth2Header(other), status=403)

    def test_get_all_contexted_activity_comments_no_read_permission(self):
        """
            Given i'm a regular user
            When i try to get all the comments from a contexted activity
            And i'm subscribed to the context
            And i don't have read permission
            I get a Forbidden exception
        """
        from max.tests.mockers import user_status_context as activity
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'restricted'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(username, activity).json['id']
        self.testapp.get('/activities/{}/comments'.format(activity_id), "", headers=oauth2Header(other), status=403)

    # Get all context comments tests

    def test_get_all_context_comments_as_manager(self):
        """
            Given i'm a Manager user
            When i try to get all the comments posted on context activities
            I succeed
        """
        from max.tests.mockers import create_context
        chash = self.create_context(create_context).json['hash']
        self.testapp.get('/contexts/{}/comments'.format(chash), "", headers=oauth2Header(test_manager), status=200)

    def test_get_all_context_comments_as_context_owner(self):
        """
            Given i'm the Owner of a contex
            When i try to get all the comments posted on context activities
            And i'm not subscribed on that context
            I get a Forbidden Exception
        """
        from max.tests.mockers import create_context
        username = 'sheldon'
        self.create_user(username)
        chash = self.create_context(create_context, owner=username).json['hash']
        self.testapp.get('/contexts/{}/comments'.format(chash), "", headers=oauth2Header(username), status=403)

    def test_get_all_context_comments(self):
        """
            Given i'm a regular user
            When i try to get all the comments posted on context activities
            And i'm subscribed to the context
            And i have read permission on the context
            I succeed
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        self.create_user(username)
        chash = self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'subscribed'}).json['hash']
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.testapp.get('/contexts/{}/comments'.format(chash), "", headers=oauth2Header(username), status=200)

    def test_get_all_context_comments_non_subscribed(self):
        """
            Given i'm a regular user
            When i try to get all the comments posted on context activities
            And i'm not subscribed to the context
            I get a Forbidden exception
        """
        from max.tests.mockers import create_context
        username = 'sheldon'
        self.create_user(username)
        chash = self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'subscribed'}).json['hash']
        self.testapp.get('/contexts/{}/comments'.format(chash), "", headers=oauth2Header(username), status=403)

    def test_get_all_context_comments_no_read_permission(self):
        """
            Given i'm a regular user
            When i try to get all the comments posted on context activities
            And i'm subscribed to the context
            And i don't have read permission
            I get a Forbidden exception
        """
        from max.tests.mockers import create_context, subscribe_context
        username = 'sheldon'
        self.create_user(username)
        chash = self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'restricted'}).json['hash']
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.testapp.get('/contexts/{}/comments'.format(chash), "", headers=oauth2Header(username), status=403)

    # Get all global comments tests

    def test_get_all_comments(self):
        """
            Given i'm a regular user
            When i try to get all the comments
            I get a Forbidden exception
        """
        username = 'sheldon'
        self.create_user(username)
        self.testapp.get('/activities/comments'.format(username), "", headers=oauth2Header(username), status=403)

    def test_get_all_comments_as_manager(self):
        """
            Given i'm a Manager user
            When i try to get all the comments
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        self.testapp.get('/activities/comments'.format(username), "", headers=oauth2Header(test_manager), status=200)
