# -*- coding: utf-8 -*-
import os
import json
import unittest
from functools import partial

from paste.deploy import loadapp
from mock import patch

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

    def tearDown(self):
        import pyramid.testing
        pyramid.testing.tearDown()

    # BEGIN TESTS

    def test_create_user(self):
        username = 'messi'
        self.testapp.post('/people/%s' % username, "", oauth2Header(test_manager), status=201)

    def test_create_user_creator_is_admin(self):
        """
            Given an admin user
            When I create a user
            Then the creator must be the admin user
        """
        username = 'messi'
        res = self.testapp.post('/people/%s' % username, "", oauth2Header(test_manager), status=201)
        self.assertEqual(res.json['creator'], test_manager)

    def test_create_user_default_fields(self):
        """
            Given an admin user
            When I create a user
            Then non-required fields with defaults are set
        """
        username = 'messi'
        res = self.testapp.post('/people/%s' % username, "", oauth2Header(test_manager), status=201)
        self.assertIn('objectType', res.json)
        self.assertIn('following', res.json)
        self.assertIn('subscribedTo', res.json)
        self.assertEqual(res.json['objectType'], 'person')

    def test_create_user_not_manager(self):
        username = 'messi'
        self.testapp.post('/people/%s' % username, "", oauth2Header('imnotallowed'), status=401)

    def test_user_exist(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s' % username, "", oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')

    def test_create_same_user_case_insensitive(self):
        username = 'messi'
        username_case = 'Messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s' % username_case, "", oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')

    def test_get_user(self):
        """ Doctest .. http:get:: /people/{username} """
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')

    def test_get_user_case_insensitive(self):
        """ Doctest .. http:get:: /people/{username} """
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/people/%s' % 'MESSI', "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('username', None), 'messi')

    def test_get_users_by_query(self):
        """ Doctest .. http:get:: /people """
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/people', json.dumps({"username": username}), oauth2Header(username), status=200)
        result = json.loads(res.text)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('username', ''), username)
        self.assertEqual(len(result[0].keys()), 4)  # Check how many fields each result has

    def test_get_user_not_me(self):
        username = 'messi'
        username_not_me = 'xavi'
        self.create_user(username)
        self.create_user(username_not_me)
        res = self.testapp.get('/people/%s' % username_not_me, "", oauth2Header(username), status=401)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'Unauthorized')

    def test_get_non_existent_user(self):
        username = 'messi'
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'UnknownUserError')

    def test_modify_user_one_parameter(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.put('/people/%s' % username, json.dumps({"displayName": "Lionel Messi"}), oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('displayName', None), 'Lionel Messi')

    def test_modify_user_several_parameters(self):
        """ Doctest .. http:put:: /people/{username} """
        username = 'messi'
        self.create_user(username)
        res = self.testapp.put('/people/%s' % username, json.dumps({"displayName": "Lionel Messi", "twitterUsername": "leomessi"}), oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('displayName', None), 'Lionel Messi')
        self.assertEqual(result.get('twitterUsername', None), 'leomessi')

    def test_modify_user_several_parameters_twice(self):
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi"})
        res = self.testapp.put('/people/%s' % username, json.dumps({"twitterUsername": "leomessi"}), oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('displayName', None), 'Lionel Messi')
        self.assertEqual(result.get('twitterUsername', None), 'leomessi')

    def test_modify_non_existent_user(self):
        username = 'messi'
        res = self.testapp.put('/people/%s' % username, json.dumps({"displayName": "Lionel Messi"}), oauth2Header(username), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'UnknownUserError')

    def test_get_all_users_with_regex(self):
        username = 'usuarimoltllarg'
        self.create_user(username)
        query = {'username': 'usuarimoltll'}
        res = self.testapp.get('/people', json.dumps(query), oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result[0].get('username', ''), username)

        query = {'username': 'usuarimo'}
        res = self.testapp.get('/people', json.dumps(query), oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result[0].get('username', ''), username)

    def test_get_all_users_with_regex_weird(self):
        username1 = 'victor.fernandez'
        self.create_user(username1)
        username2 = 'victor.fernandez.altable'
        self.create_user(username2)

        query = {'username': username1}
        res = self.testapp.get('/people', query, oauth2Header(username1), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 2)

        query = {'username': username2}
        res = self.testapp.get('/people', query, oauth2Header(username2), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)

    def test_create_own_user(self):
        username = 'messi'
        self.testapp.post('/people/%s' % username, "", oauth2Header(username), status=201)

    def test_add_device_token(self):
        username = 'messi'
        platform = 'ios'
        token = '12345678901234567890123456789012'
        self.create_user(username)
        res = self.testapp.post('/people/%s/device/%s/%s' % (username, platform, token), "", oauth2Header(username), status=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('iosDevices', []), [token])

        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('iosDevices', []), [token])

    def test_add_device_token_android(self):
        username = 'messi'
        platform = 'android'
        token = '12345678901234567890123456789012klhsdflajshdfkjashdfoq'
        self.create_user(username)
        res = self.testapp.post('/people/%s/device/%s/%s' % (username, platform, token), "", oauth2Header(username), status=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('androidDevices', []), [token])

        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('androidDevices', []), [token])

    # def test_add_device_token_invalid_token(self):
    #     username = 'messi'
    #     platform = 'ios'
    #     token = '1234'
    #     self.create_user(username)
    #     self.testapp.post('/people/%s/device/%s/%s' % (username, platform, token), "", oauth2Header(username), status=400)

    def test_delete_device_token(self):
        username = 'messi'
        platform = 'ios'
        token = '12345678901234567890123456789012'
        self.create_user(username)
        self.testapp.post('/people/%s/device/%s/%s' % (username, platform, token), "", oauth2Header(username), status=201)
        self.testapp.delete('/people/%s/device/%s/%s' % (username, platform, token), "", oauth2Header(username), status=204)
        res = self.testapp.get('/people/%s' % username, "", oauth2Header(username))
        result = json.loads(res.text)
        self.assertEqual(result.get('iosDevices'), [])
