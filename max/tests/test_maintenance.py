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
        from .mockers import group_message as message

        sender = 'messi'
        recipient = 'xavi'
        recipient2 = 'shakira'
        self.create_user(sender)
        self.create_user(recipient)
        self.create_user(recipient2)

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)

        #Hard modify group conversation directly on mongo to simulate changed permissions, displayName and tags
        conversations = self.exec_mongo_query('conversations', 'find', {})
        conversation = conversations[0]
        conversation['permissions']['write'] = 'restricted'
        conversation['displayName'] = 'Changed Name'
        conversation['tags'] = []
        conversation['participants'] = ['messi', 'xavi', 'shakira']  # Simulate ol'times structure
        self.exec_mongo_query('conversations', 'update', {'_id': conversation['_id']}, conversation)

        # Hard Put a displayName on a user
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
        self.assertEqual(res.json['talkingIn'][0]['participants'][2]['username'], 'shakira')
        self.assertListEqual(res.json['talkingIn'][0]['permissions'], ['read', 'unsubscribe', 'subscribe'])
        self.assertListEqual(res.json['talkingIn'][0]['tags'], ['group'])
        conversation_id = res.json['talkingIn'][0]['id']

        #Check context participants are updated
        res = self.testapp.get('/conversations/{}'.format(conversation_id), "", oauth2Header(sender), status=200)
        self.assertEqual(res.json['participants'][0]['displayName'], 'Lionel Messi')

        #Check user activity is updated
        res = self.testapp.get('/conversations/{}/messages'.format(conversation_id), "", oauth2Header(sender), status=200)
        self.assertEqual(res.json[0]['contexts'][0]['displayName'], 'Changed Name')

    def test_maintenance_users(self):
        username = 'messi'
        self.create_user(username)

        #Hard modify user directly on mongo to simulate wrong owner and check is wrong
        self.exec_mongo_query('users', 'update', {'username': username}, {'$set': {'_owner': 'test_manager'}})
        res = self.testapp.get('/people/{}'.format(username), "", oauth2Header(test_manager), status=200)
        self.assertEqual(res.json['owner'], 'test_manager')

        self.testapp.post('/admin/maintenance/users', "", oauth2Header(test_manager), status=200)
        res = self.testapp.get('/people/{}'.format(username), "", oauth2Header(test_manager), status=200)
        self.assertEqual(res.json['owner'], username)
