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

    # Add activity tests

    def test_add_activity_as_user(self):
        """
            Given i'm a regular user
            When i try to post an activity to my timeline
            I succeed
        """
        from max.tests.mockers import user_status as activity
        username = 'sheldon'
        self.create_user(username)
        self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)

    def test_add_activity_as_user_to_other(self):
        """
            Given i'm a regular user
            When i try to post an activity someone else's timeline
            I get a Forbidden Exceception
        """
        from max.tests.mockers import user_status as activity
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.testapp.post('/people/%s/activities' % other, json.dumps(activity), oauth2Header(username), status=403)

    def test_add_activity_as_manager(self):
        """
            Given i'm a Manager
            When i try to post a activity to an user's timeline
            I succeed
        """
        from max.tests.mockers import user_status as activity
        username = 'sheldon'
        self.create_user(username)
        self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(test_manager), status=201)

    # Add activity to context tests

    def test_add_context_activity_as_user(self):
        """
            Given i'm a regular user
            When i try to post a  activity to a context
            And i'm subscribed to that context
            And i have write permission on the subscription
            I succeed
        """
        from max.tests.mockers import subscribe_context, create_context
        from max.tests.mockers import user_status_context
        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context, permissions={'write': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context, expect=201)

    def test_add_context_activity_as_user_no_subscription(self):
        """
            Given i'm a regular user
            When i try to post a  activity to a context
            And i'm not subscribed to that context
            I get a Forbidden Exception
        """
        from max.tests.mockers import create_context
        from max.tests.mockers import user_status_context
        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context, permissions={'write': 'subscribed'})
        self.create_activity(username, user_status_context, expect=403)

    def test_add_context_activity_as_user_no_write_permission(self):
        """
            Given i'm a regular user
            When i try to post a  activity to a context
            And i'm subscribed to that context
            And i don't have write permission on the subscription
            I get a Forbidden Exception
        """
        from max.tests.mockers import subscribe_context, create_context
        from max.tests.mockers import user_status_context
        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context, permissions={'write': 'restricted'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context, expect=403)

    def test_add_context_activity_as_manager(self):
        """
            Given i'm a Manager
            When i try to post a activity to a context
            And i'm not subscribed to the context
            I succeed
        """
        from max.tests.mockers import create_context
        from max.tests.mockers import user_status_context
        self.create_context(create_context, permissions={'write': 'restricted'})
        self.create_activity(test_manager, user_status_context, expect=201)

    def test_add_context_activity_as_manager_impersonating(self):
        """
            Given i'm a Manager
            When i try to post a activity to a context
            And i'm acting as another user
            I succeed
        """
        from max.tests.mockers import subscribe_context, create_context
        from max.tests.mockers import user_status_context
        username = 'sheldon'
        self.create_user(username)
        self.create_context(create_context, permissions={'write': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context, oauth_username=test_manager, expect=201)

    def test_add_context_activity_as_owner_impersonating(self):
        """
            Given i'm the owner of a context
            When i try to post a activity to a context
            And i'm acting as another user
            I get a Forbidden Exception
        """
        from max.tests.mockers import subscribe_context, create_context
        from max.tests.mockers import user_status_context
        username = 'sheldon'
        other = 'penny'

        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed'}, owner=username)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        self.create_activity(other, user_status_context, oauth_username=username, expect=403)

    # Get user activities

    def test_get_all_activities_from_a_user(self):
        """
            Given i'm a regular user
            When i try to get all my activities
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)
        self.testapp.get('/people/{}/activities'.format(username), "", headers=oauth2Header(username), status=200)

    def test_get_all_activities_from_another_user(self):
        """
            Given i'm a regular user
            When i try to get all activities from another user (public o from shared contexts)
            I succeded
        """
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)

        self.testapp.get('/people/{}/activities'.format(other), "", headers=oauth2Header(username), status=200)

    def test_get_all_activities_from_user_as_manager(self):
        """
            Given i'm a Manager
            When i try to get all activities from a user
            I succeed
        """
        username = 'sheldon'
        self.create_user(username)

        self.testapp.get('/people/{}/activities'.format(username), "", headers=oauth2Header(test_manager), status=200)

    # Get global activities

    def test_get_all_activities_as_manager(self):
        """
            Given i'm a Manager
            When i try to get all activities
            I succeed
        """
        self.testapp.get('/activities', "", headers=oauth2Header(test_manager), status=200)

    def test_get_all_activities_as_non_manager(self):
        """
            Given i'm a regular user
            When i try to get all activities
            I get a Forbidden Exception
        """
        username = 'sheldon'
        self.create_user(username)

        self.testapp.get('/activities', "", headers=oauth2Header(username), status=403)

    # Get context activities

    def test_get_all_context_activities_as_manager(self):
        """
            Given i'm a Manager
            When i try to get all activities from a context
            And i'm not subscribed to the context
            I succeed
        """
        from max.tests.mockers import create_context

        url_hash = self.create_context(create_context).json['hash']
        self.testapp.get('/contexts/{}/activities'.format(url_hash), "", headers=oauth2Header(test_manager), status=200)

    def test_get_all_context_activities_as_subscribed_user(self):
        """
            Given i'm a regular user
            When i try to get all context activities
            And i'm subscribed to that context
            And i have read permission on that context
            I succeed
        """
        from max.tests.mockers import subscribe_context, create_context
        username = 'sheldon'

        self.create_user(username)
        url_hash = self.create_context(create_context, permissions={'read': 'subscribed'}).json['hash']
        self.admin_subscribe_user_to_context(username, subscribe_context)

        self.testapp.get('/contexts/{}/activities'.format(url_hash), "", headers=oauth2Header(username), status=200)

    def test_get_all_context_activities_as_subscribed_user_no_read(self):
        """
            Given i'm a regular user
            When i try to get all context activities
            And i'm subscribed to that context
            And i don't have read permission on that context
            I get a Forbidden Exception
        """
        from max.tests.mockers import subscribe_context, create_context
        username = 'sheldon'

        self.create_user(username)
        url_hash = self.create_context(create_context, permissions={'read': 'restricted'}).json['hash']
        self.admin_subscribe_user_to_context(username, subscribe_context)

        self.testapp.get('/contexts/{}/activities'.format(url_hash), "", headers=oauth2Header(username), status=403)

    def test_get_all_context_activities_as_non_subscribed_user(self):
        """
            Given i'm a regular user
            When i try to get all context activities
            And i'm not subscribed to that context
            I get a Forbidden Exception
        """
        from max.tests.mockers import create_context
        username = 'sheldon'

        self.create_user(username)
        url_hash = self.create_context(create_context, permissions={'read': 'restricted'}).json['hash']

        self.testapp.get('/contexts/{}/activities'.format(url_hash), "", headers=oauth2Header(username), status=403)

    # Get context activity authors

    def test_get_context_activity_authors_as_subscribed(self):
        """
            Given i'm a regular user
            When i try to get all context activities authors
            And i'm subscribed to that context
            And i have read permission on that context
            I succeed
        """
        from max.tests.mockers import subscribe_context, create_context
        username = 'sheldon'

        self.create_user(username)
        url_hash = self.create_context(create_context, permissions={'read': 'subscribed'}).json['hash']
        self.admin_subscribe_user_to_context(username, subscribe_context)

        self.testapp.get('/contexts/{}/activities/authors'.format(url_hash), "", headers=oauth2Header(username), status=200)

    # Get Activity. Image and file attachement are not tests as share the same permissions
    # as getting a single activity.

    def test_get_activity_as_other(self):
        """
            Given i'm a regular user
            When i try to get a contextless activity that i don't own
            I succeed
        """
        from max.tests.mockers import user_status
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        activity_id = self.create_activity(username, user_status, expect=201).json['id']
        self.testapp.get('/activities/{}'.format(activity_id), "", oauth2Header(other), status=200)

    def test_get_activity_as_manager(self):
        """
            Given i'm a Manager
            When i try to get a specific activity
            I succeed
        """
        from max.tests.mockers import user_status
        username = 'sheldon'
        self.create_user(username)
        activity_id = self.create_activity(username, user_status, expect=201).json['id']
        self.testapp.get('/activities/{}'.format(activity_id), "", oauth2Header(test_manager), status=200)

    def test_get_activity_as_owner(self):
        """
            Given i'm a regular user
            When i try to get an activity that i own
            I succeed
        """
        from max.tests.mockers import user_status
        username = 'sheldon'
        self.create_user(username)
        activity_id = self.create_activity(username, user_status, expect=201).json['id']
        self.testapp.get('/activities/{}'.format(activity_id), "", oauth2Header(username), status=200)

    def test_get_activity_as_subscribed(self):
        """
            Given i'm a regular user
            When i try to get an activity
            And i don't own the activity
            And i'm subscribed to the activity's context
            And i have read permission on that context
            I succeed
        """
        from max.tests.mockers import subscribe_context, create_context
        from max.tests.mockers import user_status_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(username, user_status_context, expect=201).json['id']

        self.testapp.get('/activities/{}'.format(activity_id), "", oauth2Header(other), status=200)

    def test_get_activity_as_subscribed_no_read_permission(self):
        """
            Given i'm a regular user
            When i try to get an activity
            And i'm subscribed to the activity's context
            And i don't own the activity
            And i don't have read permission on that context
            I get a Forbidden Exception
        """
        from max.tests.mockers import subscribe_context, create_context
        from max.tests.mockers import user_status_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'restricted'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(other, subscribe_context)
        activity_id = self.create_activity(username, user_status_context, expect=201).json['id']

        self.testapp.get('/activities/{}'.format(activity_id), "", oauth2Header(other), status=403)

    def test_get_activity_as_non_owner_neither_subscribed(self):
        """
            Given i'm a regular user
            When i try to get a context activity that i don't own
            And the activity is not from a context i'm subscribed to
            I get a Forbidden Exception
        """
        from max.tests.mockers import subscribe_context, create_context
        from max.tests.mockers import user_status_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'subscribed'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_id = self.create_activity(username, user_status_context, expect=201).json['id']

        self.testapp.get('/activities/{}'.format(activity_id), "", oauth2Header(other), status=403)

    def test_get_activity_as_non_owner_neither_subscribed_public_context(self):
        """
            Given i'm a regular user
            When i try to get a context activity that i don't own
            And the activity is not from a context i'm subscribed to
            I get a Forbidden Exception
        """
        from max.tests.mockers import subscribe_context, create_context
        from max.tests.mockers import user_status_context
        username = 'sheldon'
        other = 'penny'
        self.create_user(username)
        self.create_user(other)
        self.create_context(create_context, permissions={'write': 'subscribed', 'read': 'public'})
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity_id = self.create_activity(username, user_status_context, expect=201).json['id']

        self.testapp.get('/activities/{}'.format(activity_id), "", oauth2Header(other), status=200)

    # Delete activity tests

    def test_delete_activity_as_manager(self):
        """
            Given i'm a Manager
            When i try to delete an activity
            I succeed
        """
        from max.tests.mockers import user_status as activity
        username = 'sheldon'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)
        self.testapp.delete('/activities/%s' % res.json['id'], '', oauth2Header(test_manager), status=204)

    def test_delete_own_activity(self):
        """
            Given i'm a regular user
            When i try to delete an activity that i own
            I succeed
        """
        from max.tests.mockers import user_status as activity
        username = 'sheldon'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)
        self.testapp.delete('/activities/%s' % res.json['id'], '', oauth2Header(username), status=204)

    def test_delete_other_activity(self):
        """
            Given i'm a regular user
            When i try to delete an activity that i don't own
            I get a Forbidden Exception
        """
        from max.tests.mockers import user_status as activity
        username = 'sheldon'
        username2 = 'penny'
        self.create_user(username)
        self.create_user(username2)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)
        self.testapp.delete('/activities/%s' % res.json['id'], '', oauth2Header(username2), status=403)

    def test_delete_other_activity_in_context_with_granted_delete_permissions(self):
        """
           Given i'm a regular user
           When I try to delete another user activity on a context
           And i've have been granted the permission to delete on that context
           Then i suceed

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
        permission = 'delete'
        res = self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, permission), "", oauth2Header(test_manager), status=201)
        res = self.create_activity(username_not_me, user_status_context)
        self.testapp.delete('/activities/%s' % res.json['id'], '', oauth2Header(username), status=204)

    def test_delete_other_activity_in_context_as_context_owner(self):
        """
           Given i'm a regular user
           When I try to delete another user activity on a context
           And i'm the owner of the context
           And i don't have explicit permission to delete
           Then i get a Forbidden Exception

        """
        from max.tests.mockers import user_status_context
        from max.tests.mockers import subscribe_context, create_context

        username = 'sheldon'
        username_not_me = 'penny'
        self.create_user(username)
        self.create_user(username_not_me)
        self.create_context(create_context, owner=username)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username_not_me, subscribe_context)
        res = self.create_activity(username_not_me, user_status_context)
        self.testapp.delete('/activities/%s' % res.json['id'], '', oauth2Header(username), status=403)
