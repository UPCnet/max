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
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('messages')
        self.app.registry.max_store.security.insert(test_default_security)
        self.app.registry.max_security = test_default_security
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

    # BEGIN TESTS
    def test_get_all_users_admin(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.get('/people', "", oauth2Header(test_manager))
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('username'), 'messi')

    def test_admin_post_activity_without_context(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(user_status), oauth2Header(test_manager))
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None), None)

    def test_admin_post_activity_with_context(self):
        """ doctest .. http:post:: /people/{username}/activities """
        from .mockers import subscribe_context
        from .mockers import user_status_context
        from .mockers import create_context

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(user_status_context), oauth2Header(test_manager))
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('username', None), 'messi')
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], subscribe_context['object']['url'])

    def test_admin_post_activity_with_context_as_actor(self):
        """ doctest .. http:post:: /contexts/{hash}/activities """
        from .mockers import subscribe_context
        from .mockers import user_status_context
        from .mockers import create_context
        from hashlib import sha1
        self.create_context(create_context)
        url_hash = sha1(create_context['url']).hexdigest()
        res = self.testapp.post('/contexts/%s/activities' % url_hash, json.dumps(user_status_context), oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('actor', None).get('hash', None), url_hash)
        self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('contexts', None)[0]['url'], subscribe_context['object']['url'])

    def test_get_security(self):
        res = self.testapp.get('/admin/security', "", status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].get('roles', None).get('Manager')[0], 'test_manager')

    def test_security_add_user_to_role(self):
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=201)
        self.assertListEqual(['messi', 'test_manager'], res.json)

    def test_security_add_user_to_non_allowed_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('WrongRole', username), "", oauth2Header(test_manager), status=400)

    def test_security_remove_user_from_non_allowed_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.delete('/admin/security/roles/%s/users/%s' % ('WrongRole', username), "", oauth2Header(test_manager), status=400)

    def test_security_add_user_to_role_already_has_role(self):
        res = self.testapp.post('/admin/security/roles/%s/users/%s' % ('Manager', 'test_manager'), "", oauth2Header(test_manager), status=200)
        self.assertListEqual(['test_manager'], res.json)

    def test_security_remove_user_from_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=201)
        res = self.testapp.delete('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=200)
        self.assertListEqual(['test_manager'], res.json)

    def test_security_remove_user_from_role_user_not_in_role(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.delete('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=404)

    def test_security_add_user_to_role_check_security_reloaded(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.get('/activities', "", oauth2Header(username), status=404)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=201)
        self.testapp.get('/activities', "", oauth2Header(username), status=200)

    def test_security_remove_user_from_role_check_security_reloaded(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.post('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=201)
        self.testapp.get('/activities', "", oauth2Header(username), status=200)
        self.testapp.delete('/admin/security/roles/%s/users/%s' % ('Manager', username), "", oauth2Header(test_manager), status=200)
        self.testapp.get('/activities', "", oauth2Header(username), status=404)

    def test_get_other_activities(self):
        from .mockers import user_status_context
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_user(test_manager)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)
        self.testapp.get('/people/%s/activities' % (username), '', oauth2Header(test_manager), status=200)

    def test_delete_user(self):
        username = 'messi'
        self.create_user(username)
        self.testapp.delete('/people/%s' % username, '', oauth2Header(test_manager), status=204)

    def test_delete_inexistent_user(self):
        username = 'messi'
        username2 = 'xavi'
        self.create_user(username)
        self.testapp.delete('/people/%s' % username2, '', oauth2Header(test_manager), status=404)

    def test_admin_delete_inexistent_activity(self):
        fake_id = '519200000000000000000000'
        self.testapp.delete('/activities/%s' % (fake_id), '', oauth2Header(test_manager), status=404)

    def test_admin_activities_search_by_context(self):
        """
        """
        from .mockers import user_status
        from .mockers import context_query
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)
        self.create_activity(username, user_status)

        res = self.testapp.get('/people/%s/activities' % username, context_query, oauth2Header(test_manager), status=200)
        result = json.loads(res.text)
        self.assertEqual(len(result), 1)

    # def test_admin_post_activity_with_unauthorized_context_type_as_actor(self):
    #     from .mockers import create_unauthorized_context
    #     from hashlib import sha1

    #     result = self.create_context(create_invalid_context, expect=201)
    #     import ipdb;ipdb.set_trace()
        # url_hash = sha1(create_invalid_context['object']['url']).hexdigest()
        # res = self.testapp.post('/contexts/%s/activities' % url_hash, json.dumps(user_status_context), oauth2Header(test_manager))
        # result = json.loads(res.text)
        # self.assertEqual(result.get('actor', None).get('hash', None), url_hash)
        # self.assertEqual(result.get('object', None).get('objectType', None), 'note')
        # self.assertEqual(result.get('contexts', None)[0], subscribe_context['object'])

    def test_get_users_twitter_enabled(self):
        """ Doctest .. http:get:: /people """
        username = 'messi'
        username2 = 'xavi'
        self.create_user(username)
        self.create_user(username2)
        self.modify_user(username, {"twitterUsername": "messipowah"})
        res = self.testapp.get('/people', {"twitter_enabled": True}, oauth2Header(test_manager), status=200)

        self.assertEqual(len(res.json), 1)

    def test_get_context_twitter_enabled(self):
        from .mockers import create_context, create_contextA
        self.create_context(create_context)
        self.create_context(create_contextA)
        self.modify_context(create_context['url'], {"twitterHashtag": "assignatura1", "twitterUsername": "maxupcnet"})

        res = self.testapp.get('/contexts', {"twitter_enabled": True}, oauth2Header(test_manager), status=200)

        self.assertEqual(len(res.json), 1)

    def test_maintenance_keywords(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username, displayName='Lionel messi')
        self.create_activity(username, user_status)

        # Hard modify keywords directly on mongodb to simulate bad keywords
        activities = self.exec_mongo_query('activity', 'find', {})
        activity = activities[0]
        del activity['_keywords']
        activity['object']['_keywords'] = []
        self.exec_mongo_query('activity', 'update', {'_id': activities[0]['_id']}, activity)

        self.testapp.post('/admin/maintenance/keywords', "", oauth2Header(test_manager), status=200)
        res = self.testapp.get('/activities/%s' % activity['_id'], "", oauth2Header(username), status=200)

        expected_keywords = [u'canvi', u'creaci\xf3', u'estatus', u'lionel', u'messi', u'testejant']
        response_keywords = res.json['keywords']
        response_keywords.sort()
        self.assertListEqual(expected_keywords, response_keywords)

    def test_maintenance_dates(self):
        from .mockers import user_status, user_comment
        username = 'messi'
        self.create_user(username, displayName='Lionel messi')
        res = self.create_activity(username, user_status)
        self.testapp.post('/activities/%s/comments' % str(res.json['id']), json.dumps(user_comment), oauth2Header(username), status=201)
        res = self.testapp.post('/activities/%s/comments' % str(res.json['id']), json.dumps(user_comment), oauth2Header(username), status=201)

        # Hard modify keywords directly on mongodb to simulate bad keywords
        activities = self.exec_mongo_query('activity', 'find', {'verb': 'post'})
        activity = activities[0]

        #simulate ancient commented field with wrong date
        activity['commented'] = activity['published']
        del activity['lastComment']
        self.exec_mongo_query('activity', 'update', {'_id': activities[0]['_id']}, activity)

        self.testapp.post('/admin/maintenance/dates', "", oauth2Header(test_manager), status=200)
        res = self.testapp.get('/activities/%s' % activity['_id'], "", oauth2Header(username), status=200)

        self.assertEqual(res.json['lastComment'], res.json['replies'][-1]['id'])

    def test_maintenance_subscriptions(self):
        from .mockers import create_context
        from .mockers import subscribe_context, user_status_context
        from hashlib import sha1

        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='subscribed', write='subscribed', subscribe='restricted', invite='restricted'))
        chash = sha1(create_context['url']).hexdigest()
        self.admin_subscribe_user_to_context(username, subscribe_context)
        self.create_activity(username, user_status_context)

        #Hard modify context directly on mongo to simulate changed permissions, displayName and tags
        contexts = self.exec_mongo_query('contexts', 'find', {'hash': chash})
        context = contexts[0]
        context['permissions']['write'] = 'restricted'
        context['displayName'] = 'Changed Name'
        context['tags'].append('new tag')
        self.exec_mongo_query('contexts', 'update', {'_id': context['_id']}, context)
        self.testapp.post('/admin/maintenance/subscriptions', "", oauth2Header(test_manager), status=200)

        #Check user subscription is updated
        res = self.testapp.get('/people/{}'.format(username), "", oauth2Header(username), status=200)
        self.assertEqual(res.json['subscribedTo'][0]['displayName'], 'Changed Name')
        self.assertListEqual(res.json['subscribedTo'][0]['tags'], ['Assignatura', 'new tag'])
        self.assertListEqual(res.json['subscribedTo'][0]['permissions'], ['read'])

        #Check user activity is updated
        res = self.testapp.get('/people/{}/timeline'.format(username), "", oauth2Header(username), status=200)
        self.assertEqual(res.json[0]['contexts'][0]['displayName'], 'Changed Name')
        self.assertListEqual(res.json[0]['contexts'][0]['tags'], ['Assignatura', 'new tag'])

    def test_maintenance_conversations(self):
        from .mockers import message

        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)

        #Hard modify conversation directly on mongo to simulate changed permissions, displayName and tags
        conversations = self.exec_mongo_query('conversations', 'find', {})
        conversation = conversations[0]
        conversation['permissions']['write'] = 'restricted'
        conversation['displayName'] = 'Changed Name'
        conversation['participants'] = ['messi', 'xavi', 'iniesta']
        self.exec_mongo_query('conversations', 'update', {'_id': conversation['_id']}, conversation)

        # Put a displayName on the user
        users = self.exec_mongo_query('users', 'find', {'username': 'messi'})
        user = users[0]
        user['displayName'] = 'Lionel Messi'
        self.exec_mongo_query('users', 'update', {'_id': user['_id']}, user)

        self.testapp.post('/admin/maintenance/conversations', "", oauth2Header(test_manager), status=200)

        #Check user subscription is updated
        res = self.testapp.get('/people/{}'.format(sender), "", oauth2Header(sender), status=200)
        self.assertEqual(res.json['talkingIn'][0]['displayName'], 'Changed Name')
        self.assertEqual(res.json['talkingIn'][0]['participants'][0]['username'], 'messi')
        self.assertEqual(res.json['talkingIn'][0]['participants'][1]['username'], 'xavi')
        self.assertEqual(res.json['talkingIn'][0]['participants'][2]['username'], 'iniesta')
        self.assertListEqual(res.json['talkingIn'][0]['permissions'], ['read', 'unsubscribe'])
        conversation_id = res.json['talkingIn'][0]['id']

        #Check context participants are updated
        res = self.testapp.get('/conversations/{}'.format(conversation_id), "", oauth2Header(sender), status=200)
        self.assertEqual(res.json['participants'][0]['displayName'], 'Lionel Messi')

        #Check user activity is updated
        res = self.testapp.get('/conversations/{}/messages'.format(conversation_id), "", oauth2Header(sender), status=200)
        self.assertEqual(res.json[0]['contexts'][0]['displayName'], 'Changed Name')

