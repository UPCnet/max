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

    def test_create_context(self):
        """ doctests .. http:post:: /contexts"""
        from .mockers import create_context
        new_context = dict(create_context)
        self.testapp.post('/contexts', json.dumps(new_context), oauth2Header(test_manager), status=201)

    def test_create_context_creator_is_admin(self):
        """
            Given a admin user
            When I create a context
            Then the creator of the context is the admin user
        """
        from .mockers import create_context
        res = self.testapp.post('/contexts', json.dumps(create_context), oauth2Header(test_manager), status=201)
        self.assertEqual(res.json['creator'], test_manager)

    def test_create_context_default_fields(self):
        """
            Given an admin user
            When I create a context
            Then non-required fields with defaults are set
        """
        from .mockers import create_context
        res = self.testapp.post('/contexts', json.dumps(create_context), oauth2Header(test_manager), status=201)
        self.assertIn('permissions', res.json)
        self.assertIn('tags', res.json)
        self.assertIn('objectType', res.json)
        self.assertEqual(res.json['objectType'], 'context')

    def test_post_activity_with_public_context(self):
        """ Post an activity to a context which allows everyone to read and write
        """
        from .mockers import subscribe_context, create_context
        from .mockers import user_status_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)

        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], subscribe_context['object']['url'])

    def test_post_activity_with_private_read_write_context(self):
        """ Post an activity to a context which needs the user to be subscribed to read and write
            and we have previously subscribed the user.
        """
        from .mockers import subscribe_context, create_context
        from .mockers import user_status_context
        username = 'messi'
        self.create_user(username)
        context_permissions = dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted')
        self.create_context(create_context, permissions=context_permissions)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)

        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], subscribe_context['object']['url'])

    def test_post_activity_with_private_read_context(self):
        """ Try to post an activity to a context which needs the user to be subscribed to read
            but needs to explicitly give write permission on the user to post and we have previously
            subscribed the user but not given write permission.
        """
        from .mockers import subscribe_context, create_context
        from .mockers import user_status_context
        username = 'messi'
        self.create_user(username)
        context_permissions = dict(read='subscribed', write='restricted', subscribe='restricted', invite='restricted')
        self.create_context(create_context, permissions=context_permissions)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context, expect=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_add_public_context(self):
        from hashlib import sha1
        from .mockers import create_context
        res = self.testapp.post('/contexts', json.dumps(create_context), oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context['url']).hexdigest()
        self.assertEqual(result.get('hash', None), url_hash)

    def test_add_invalid_context(self):
        from .mockers import create_invalid_context
        self.create_context(create_invalid_context, expect=400)

    def test_add_uri_context_without_displayName(self):
        """
            Add a Uri context without a displayName and check that the default displayName is set
            with the url from the uri object
        """
        from .mockers import create_context_without_displayname
        res = self.create_context(create_context_without_displayname, expect=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('displayName', None), create_context_without_displayname['url'])

    def test_add_public_context_with_all_params(self):
        from hashlib import sha1
        from .mockers import create_context_full
        res = self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context_full['url']).hexdigest()
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('displayName', None), create_context_full['displayName'])
        self.assertEqual(result.get('twitterHashtag', None), create_context_full['twitterHashtag'])
        self.assertEqual(result.get('twitterUsername', None), create_context_full['twitterUsername'])

    def test_context_exists(self):
        """ doctest .. http:get:: /contexts/{hash} """
        from hashlib import sha1
        from .mockers import create_context
        url_hash = sha1(create_context['url']).hexdigest()
        self.create_context(create_context)
        res = self.testapp.get('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)

    def test_create_context_that_already_exists(self):
        """ doctest .. http:get:: /contexts/{hash} """
        from hashlib import sha1
        from .mockers import create_context
        url_hash = sha1(create_context['url']).hexdigest()
        self.testapp.post('/contexts', json.dumps(create_context), oauth2Header(test_manager), status=201)
        res = self.testapp.post('/contexts', json.dumps(create_context), oauth2Header(test_manager), status=200)
        self.assertEqual(res.json.get('hash', None), url_hash)

    def test_modify_context(self):
        """ doctest .. http:put:: /contexts/{hash} """
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1"}), oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('twitterHashtag', None), 'assignatura1')

    def test_modify_inexistent_context(self):
        """ doctest .. http:put:: /contexts/{hash} """
        url_hash = '0000000000000'
        self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1"}), oauth2Header(test_manager), status=404)

    def test_modify_context_with_twitter_username(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1", "twitterUsername": "maxupcnet"}), oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('twitterHashtag', None), 'assignatura1')
        self.assertEqual(result.get('twitterUsername', None), 'maxupcnet')
        self.assertEqual(result.get('twitterUsernameId', None), '526326641')

    def test_get_context_tags(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.get('/contexts/%s/tags' % url_hash, "", oauth2Header(test_manager), status=200)
        self.assertEqual(res.json, ['Assignatura'])

    def test_update_context_tags_updates_existing_tags(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.put('/contexts/%s/tags' % url_hash, json.dumps(['prova']), oauth2Header(test_manager), status=200)
        self.assertEqual(res.json, ['Assignatura', 'prova'])

    def test_update_context_tags_updates_existing_activites_tags(self):
        from hashlib import sha1
        from .mockers import create_context, subscribe_context, user_status_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)
        self.testapp.put('/contexts/%s/tags' % url_hash, json.dumps(['prova']), oauth2Header(test_manager), status=200)
        res = self.testapp.get('/contexts/%s/activities' % url_hash, "", oauth2Header(username), status=200)
        self.assertEqual(res.json[0]['contexts'][0]['tags'], ['Assignatura', 'prova'])

    def test_update_context_tags_updates_existing_subscription_tags(self):
        from hashlib import sha1
        from .mockers import create_context, subscribe_context, user_status_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)
        self.testapp.put('/contexts/%s/tags' % url_hash, json.dumps(['prova']), oauth2Header(test_manager), status=200)
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username), status=200)
        self.assertEqual(res.json['subscribedTo'][0]['tags'], ['Assignatura', 'prova'])

    def test_clear_context_tags(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.delete('/contexts/%s/tags' % url_hash, "", oauth2Header(test_manager), status=200)
        self.assertEqual(res.json, [])

    def test_remove_context_tag(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        self.testapp.put('/contexts/%s/tags' % url_hash, json.dumps(['prova']), oauth2Header(test_manager), status=200)
        self.testapp.delete('/contexts/%s/tags/%s' % (url_hash, 'Assignatura'), "", oauth2Header(test_manager), status=204)

    def test_modify_context_displayName_updates_subscription(self):
        from hashlib import sha1
        from .mockers import create_context, subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='restricted', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context, expect=201)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"displayName": "New Name"}), oauth2Header(test_manager), status=200)
        res = self.testapp.get('/people/%s/subscriptions' % username, '', oauth2Header(username), status=200)
        self.assertEqual(res.json[0]['displayName'], 'New Name')

    def test_modify_context_unsetting_property(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        self.modify_context(create_context['url'], {"twitterHashtag": "assignatura1", "twitterUsername": "maxupcnet"})
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura4", "twitterUsername": ""}), oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('twitterHashtag', None), 'assignatura4')
        self.assertEqual(result.get('twitterUsername', None), None)
        self.assertEqual(result.get('twitterUsernameId', None), None)

    def test_delete_context(self):
        """ doctest .. http:delete:: /contexts/{hash} """
        from hashlib import sha1
        from .mockers import create_context
        url_hash = sha1(create_context['url']).hexdigest()
        self.create_context(create_context)
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)

    def test_deleted_context_is_really_deleted(self):
        from hashlib import sha1
        from .mockers import create_context
        url_hash = sha1(create_context['url']).hexdigest()
        self.create_context(create_context)
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)
        res = self.testapp.get('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=404)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'ObjectNotFound')

    def test_delete_inexistent_context(self):
        """ doctest .. http:delete:: /contexts/{hash} """
        url_hash = '00000000000000'
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=404)

    def test_delete_only_deleted_specified_context(self):
        from hashlib import sha1
        from .mockers import create_context, create_contextA
        self.create_context(create_context)
        self.create_context(create_contextA)

        url_hash = sha1(create_context['url']).hexdigest()
        url_hashA = sha1(create_contextA['url']).hexdigest()
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)
        res = self.testapp.get('/contexts/%s' % url_hashA, "", oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hashA)

    def test_delete_context_removes_subscription_from_user(self):
        """
        """
        from hashlib import sha1
        from .mockers import subscribe_context, subscribe_contextA
        from .mockers import create_context, create_contextA
        from .mockers import user_status_context, user_status_contextA
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.create_context(create_contextA)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username, subscribe_contextA)
        self.create_activity(username, user_status_context)
        self.create_activity(username, user_status_contextA)

        url_hash = sha1(create_context['url']).hexdigest()
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)

        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')
        self.assertEqual(len(result.get('subscribedTo', [])), 1)
        self.assertEqual(result.get('subscribedTo', [])[0]['url'], subscribe_contextA['object']['url'])

    def test_user_cannot_see_activity_from_deleted_context(self):
        """
        """
        from hashlib import sha1
        from .mockers import subscribe_context
        from .mockers import create_context
        from .mockers import user_status_context
        from .mockers import context_query
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)

        url_hash = sha1(create_context['url']).hexdigest()
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)
        self.testapp.get('/contexts/%s/activities' % (context_query['context']), '',  oauth2Header(username), status=404)

    def test_user_cannot_see_own_activity_from_deleted_context_in_timeline(self):
        """
        """
        from hashlib import sha1
        from .mockers import subscribe_context
        from .mockers import create_context
        from .mockers import user_status_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)

        url_hash = sha1(create_context['url']).hexdigest()
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)
        res = self.testapp.get('/people/%s/timeline' % username, {}, oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 0)

    def test_add_private_rw_context(self):
        from hashlib import sha1
        from .mockers import create_context_private_rw
        res = self.testapp.post('/contexts', json.dumps(create_context_private_rw), oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context_private_rw['url']).hexdigest()
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('permissions', None), create_context_private_rw['permissions'])

    def test_add_private_r_context(self):
        from hashlib import sha1
        from .mockers import create_context_private_r
        res = self.testapp.post('/contexts', json.dumps(create_context_private_r), oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context_private_r['url']).hexdigest()
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('permissions', None), create_context_private_r['permissions'])

    def test_check_permissions_on_subscribed_rw_context(self):
        from .mockers import create_context_private_rw, subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_rw)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(len(result.get('subscribedTo', [])), 1)
        self.assertEqual(result.get('subscribedTo', {})[0]['url'], subscribe_context['object']['url'])
        self.assertEqual('read' in result.get('subscribedTo', {})[0]['permissions'], True)
        self.assertEqual('write' in result.get('subscribedTo', {})[0]['permissions'], True)

    def test_check_permissions_on_subscribed_write_restricted_context(self):
        from .mockers import create_context_private_r, subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(len(result.get('subscribedTo', [])), 1)
        self.assertEqual(result.get('subscribedTo', {})[0]['url'], subscribe_context['object']['url'])
        self.assertEqual('read' in result.get('subscribedTo', {})[0]['permissions'], True)
        self.assertEqual('write' not in result.get('subscribedTo', {})[0]['permissions'], True)

    def test_post_on_subscribed_write_restricted_context_without_write_permission(self):
        from .mockers import create_context_private_r, subscribe_context, user_status_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context, expect=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_post_on_subscribed_rw_context(self):
        from .mockers import create_context_private_rw, subscribe_context, user_status_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_rw)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.create_activity(username, user_status_context)
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], user_status_context['contexts'][0]['url'])

    def test_grant_write_permission_on_write_restricted_context(self):
        """ doctest .. http:put:: /contexts/{hash}/permissions/{username}/{permission} """
        from .mockers import create_context_private_r, subscribe_context
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        chash = sha1(create_context_private_r['url']).hexdigest()
        permission = 'write'
        res = self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, permission), "", oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        self.assertEqual('read' in result['permissions'], True)
        self.assertEqual('write' in result['permissions'], True)

    def test_revoke_write_permission_on_write_restricted_context(self):
        """ doctest .. http:delete:: /contexts/{hash}/permissions/{username}/{permission} """
        from .mockers import create_context_private_r, subscribe_context
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        chash = sha1(create_context_private_r['url']).hexdigest()
        permission = 'write'
        res = self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, permission), "", oauth2Header(test_manager), status=201)
        res = self.testapp.delete('/contexts/%s/permissions/%s/%s' % (chash, username, permission), "", oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        self.assertEqual('read' in result['permissions'], True)
        self.assertEqual('write' not in result['permissions'], True)

    def test_grant_write_permission_on_non_subscribed_context(self):
        from .mockers import create_context_private_r
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        chash = sha1(create_context_private_r['url']).hexdigest()
        permission = 'write'
        res = self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, permission), "", oauth2Header(test_manager), status=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_grant_invalid_permission_on_subscribed_context(self):
        from .mockers import create_context_private_r, subscribe_context
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        chash = sha1(create_context_private_r['url']).hexdigest()
        permission = 'badpermission'
        res = self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, permission), "", oauth2Header(test_manager), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'InvalidPermission')

    def test_reset_user_subscription_to_default_permissions(self):
        from .mockers import create_context_private_r, subscribe_context
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        chash = sha1(create_context_private_r['url']).hexdigest()
        permission = 'write'
        self.testapp.put('/contexts/%s/permissions/%s/%s' % (chash, username, permission), "", oauth2Header(test_manager), status=201)
        res = self.testapp.post('/contexts/%s/permissions/%s/defaults' % (chash, username), "", oauth2Header(test_manager), status=200)

        result = json.loads(res.text)
        self.assertEqual('read' in result['permissions'], True)
        self.assertEqual('write' in result['permissions'], False)

    def test_get_context_subscriptions(self):
        from .mockers import create_context_private_r, subscribe_context
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        chash = sha1(create_context_private_r['url']).hexdigest()
        res = self.testapp.get('/contexts/%s/subscriptions' % (chash), "", oauth2Header(test_manager), status=200)
        result = json.loads(res.text)

        self.assertEqual(result[0].get('username', ''), 'messi')
