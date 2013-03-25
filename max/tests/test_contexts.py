# -*- coding: utf-8 -*-
import os
import json
import unittest

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, oauth2Header
from max.tests import test_manager, test_default_security


class mock_post(object):

    def __init__(self, *args, **kwargs):
        pass

    text = ""
    status_code = 200


@patch('requests.post', new=mock_post)
class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        from webtest import TestApp
        self.testapp = TestApp(self.app)

    # BEGIN TESTS

    def test_create_context(self):
        """ doctests .. http:post:: /contexts"""
        from .mockers import create_context
        permissions = dict(read='public', write='restricted', subscribe='restricted', invite='restricted')
        default_permissions = dict(read='public', write='public', join='public', invite='subscribed')
        new_context = dict(create_context)
        if 'permissions' not in new_context:
            new_context['permissions'] = default_permissions
        if permissions:
            new_context['permissions'].update(permissions)
        self.testapp.post('/contexts', json.dumps(new_context), oauth2Header(test_manager), status=201)

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
        self.assertEqual(result.get('contexts', None)[0]['object'], subscribe_context['object'])

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
        self.assertEqual(result.get('contexts', None)[0]['object'], subscribe_context['object'])

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
        url_hash = sha1(create_context['object']['url']).hexdigest()
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
        self.assertEqual(result.get('displayName', None), create_context_without_displayname['object']['url'])

    def test_add_public_context_with_all_params(self):
        from hashlib import sha1
        from .mockers import create_context_full
        res = self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context_full['object']['url']).hexdigest()
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('displayName', None), create_context_full['displayName'])
        self.assertEqual(result.get('twitterHashtag', None), create_context_full['twitterHashtag'])
        self.assertEqual(result.get('twitterUsername', None), create_context_full['twitterUsername'])

    def test_context_exists(self):
        """ doctest .. http:get:: /contexts/{hash} """
        from hashlib import sha1
        from .mockers import create_context
        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.create_context(create_context)
        res = self.testapp.get('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)

    def test_modify_context(self):
        """ doctest .. http:put:: /contexts/{hash} """
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1"}), oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('twitterHashtag', None), 'assignatura1')

    def test_modify_context_with_twitter_username(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1", "twitterUsername": "maxupcnet"}), oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('twitterHashtag', None), 'assignatura1')
        self.assertEqual(result.get('twitterUsername', None), 'maxupcnet')
        self.assertEqual(result.get('twitterUsernameId', None), '526326641')

    def test_modify_context_unsetting_property(self):
        from hashlib import sha1
        from .mockers import create_context
        self.create_context(create_context)
        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.modify_context(create_context['object']['url'], {"twitterHashtag": "assignatura1", "twitterUsername": "maxupcnet"})
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
        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.create_context(create_context)
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)

    def test_deleted_context_is_really_deleted(self):
        from hashlib import sha1
        from .mockers import create_context
        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.create_context(create_context)
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)
        res = self.testapp.get('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=404)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'ObjectNotFound')

    def test_delete_only_deleted_specified_context(self):
        from hashlib import sha1
        from .mockers import create_context, create_contextA
        self.create_context(create_context)
        self.create_context(create_contextA)

        url_hash = sha1(create_context['object']['url']).hexdigest()
        url_hashA = sha1(create_contextA['object']['url']).hexdigest()
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

        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)

        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')
        self.assertEqual(result.get('subscribedTo', {}).get('totalItems', None), 1)
        self.assertEqual(result.get('subscribedTo', {}).get('items', [None, ])[0]['object'], subscribe_contextA['object'])

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

        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)
        self.testapp.get('/activities', context_query, oauth2Header(username), status=404)

    def test_user_only_sees_own_activity_from_deleted_context_in_timeline(self):
        """
        """
        from hashlib import sha1
        from .mockers import subscribe_context
        from .mockers import create_context
        from .mockers import user_status_context
        username = 'messi'
        username2 = 'xavi'
        self.create_user(username)
        self.create_user(username2)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.admin_subscribe_user_to_context(username2, subscribe_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username2, user_status_context)

        url_hash = sha1(create_context['object']['url']).hexdigest()
        self.testapp.delete('/contexts/%s' % url_hash, "", oauth2Header(test_manager), status=204)
        res = self.testapp.get('/people/%s/timeline' % username, {}, oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 1)
        self.assertEqual(result.get('items', None)[0]['actor']['username'], username)

    def test_add_private_rw_context(self):
        from hashlib import sha1
        from .mockers import create_context_private_rw
        res = self.testapp.post('/contexts', json.dumps(create_context_private_rw), oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context_private_rw['object']['url']).hexdigest()
        self.assertEqual(result.get('hash', None), url_hash)
        self.assertEqual(result.get('permissions', None), create_context_private_rw['permissions'])

    def test_add_private_r_context(self):
        from hashlib import sha1
        from .mockers import create_context_private_r
        res = self.testapp.post('/contexts', json.dumps(create_context_private_r), oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        url_hash = sha1(create_context_private_r['object']['url']).hexdigest()
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
        self.assertEqual(result.get('subscribedTo', {}).get('totalItems'), 1)
        self.assertEqual(result.get('subscribedTo', {}).get('items')[0]['object']['url'], subscribe_context['object']['url'])
        self.assertEqual('read' in result.get('subscribedTo', {}).get('items')[0]['permissions'], True)
        self.assertEqual('write' in result.get('subscribedTo', {}).get('items')[0]['permissions'], True)

    def test_check_permissions_on_subscribed_write_restricted_context(self):
        from .mockers import create_context_private_r, subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('subscribedTo', {}).get('totalItems'), 1)
        self.assertEqual(result.get('subscribedTo', {}).get('items')[0]['object']['url'], subscribe_context['object']['url'])
        self.assertEqual('read' in result.get('subscribedTo', {}).get('items')[0]['permissions'], True)
        self.assertEqual('write' not in result.get('subscribedTo', {}).get('items')[0]['permissions'], True)

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
        self.assertEqual(result.get('contexts', None)[0]['object']['url'], user_status_context['contexts'][0]['url'])

    def test_grant_write_permission_on_write_restricted_context(self):
        """ doctest .. http:put:: /contexts/{hash}/permissions/{username}/{permission} """
        from .mockers import create_context_private_r, subscribe_context
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        chash = sha1(create_context_private_r['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s/permissions/%s/write' % (chash, username), "", oauth2Header(test_manager), status=201)
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
        chash = sha1(create_context_private_r['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s/permissions/%s/write' % (chash, username), "", oauth2Header(test_manager), status=201)
        res = self.testapp.delete('/contexts/%s/permissions/%s/write' % (chash, username), "", oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual('read' in result['permissions'], True)
        self.assertEqual('write' not in result['permissions'], True)

    def test_grant_write_permission_on_non_subscribed_context(self):
        from .mockers import create_context_private_r
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        chash = sha1(create_context_private_r['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s/permissions/%s/write' % (chash, username), "", oauth2Header(test_manager), status=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_grant_invalid_permission_on_subscribed_context(self):
        from .mockers import create_context_private_r, subscribe_context
        from hashlib import sha1
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_private_r)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        chash = sha1(create_context_private_r['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s/permissions/%s/badpermission' % (chash, username), "", oauth2Header(test_manager), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'InvalidPermission')
