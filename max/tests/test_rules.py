# -*- coding: utf-8 -*-
import unittest
import os
from paste.deploy import loadapp
import base64
import json

from mock import patch
from maxrules import config

config.mongodb_db_name = 'tests'


class mock_post_obj(object):

    def __init__(self, *args, **kwargs):
        self.text = kwargs['text']
        self.status_code = kwargs['status_code']


class RulesTests(unittest.TestCase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        from webtest import TestApp
        self.testapp = TestApp(self.app)
        self.patched = patch('requests.post', new=self.mock_post)
        self.patched.start()

    def mock_post(self, *args, **kwargs):
        if '/admin/people/messi/activities' in args[0]:
            # Fake the requests.post thorough the self.testapp instance, and test result later in test
            res = self.testapp.post('/admin/people/%s/activities' % 'messi', args[1], basicAuthHeader('admin', 'admin'), status=201)
            return mock_post_obj(text=res.text, status_code=201)

        return mock_post_obj(text='', status_code=200)

    def create_user(self, username):
        res = self.testapp.post('/people/%s' % username, "", basicAuthHeader('operations', 'operations'), status=201)
        return res

    def modify_user(self, username, properties):
        res = self.testapp.put('/people/%s' % username, json.dumps(properties), oauth2Header(username))
        return res

    def create_activity(self, username, activity, oauth_username=None, expect=201):
        oauth_username = oauth_username != None and oauth_username or username
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(oauth_username), status=expect)
        return res

    def create_context(self, context, permissions=None, expect=201):
        default_permissions = dict(read='public', write='public', join='public', invite='subscribed')
        new_context = dict(context)
        if 'permissions' not in new_context:
            new_context['permissions'] = default_permissions
        if permissions:
            new_context['permissions'].update(permissions)
        res = self.testapp.post('/contexts', json.dumps(new_context), basicAuthHeader('operations', 'operations'), status=expect)
        return res

    def modify_context(self, context, properties):
        from hashlib import sha1
        url_hash = sha1(context).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterHashtag": "assignatura1"}), basicAuthHeader('operations', 'operations'), status=200)
        return res

    def subscribe_user_to_context(self, username, context, expect=201):
        res = self.testapp.post('/people/%s/subscriptions' % username, json.dumps(context), basicAuthHeader('operations', 'operations'), status=expect)
        return res

    # Tests

    def test_process_new_tweet(self):
        from maxrules.tasks import processTweet
        from .mockers import create_contextA, subscribe_contextA
        username = 'messi'
        self.create_user(username)
        self.modify_user(username, {"displayName": "Lionel Messi", "twitterUsername": "leomessi"})
        context_permissions = dict(read='subscribed', write='subscribed', join='restricted', invite='restricted')
        self.create_context(create_contextA, permissions=context_permissions)
        self.modify_context(create_contextA['url'], {"twitterHashtag": "assignatura1"})
        self.subscribe_user_to_context(username, subscribe_contextA)

        processTweet('leomessi', 'Ehteee, acabo de batir el récor de goles en el Barça #atenea #assignatura1')

        res = self.testapp.get('/people/%s/timeline' % username, "", oauth2Header(username), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('totalItems', None), 1)
        self.assertEqual(result.get('items', None)[0].get('actor', None).get('username'), 'messi')
        self.assertEqual(result.get('items', None)[0].get('object', None).get('objectType', None), 'note')
        self.assertEqual(result.get('items', None)[0].get('contexts', None)[0], subscribe_contextA['object'])


def basicAuthHeader(username, password):
    base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
    return dict(Authorization="Basic %s" % base64string)


def oauth2Header(username):
    return {"X-Oauth-Token": "jfa1sDF2SDF234", "X-Oauth-Username": username, "X-Oauth-Scope": "widgetcli"}


# import unittest
# from pyramid import testing

# testSettings = {'max.enforce_settings': True,
#                 'max.oauth_check_endpoint': 'http://localhost:8080/checktoken',
#                 'mongodb.url': 'mongodb://localhost',
#                 'mongodb.db_name': 'tests'}


# class RulesTests(unittest.TestCase):

#     def setUp(self):
#         self.config = testing.setUp(settings=testSettings)
#         self.config.include('max')

#     def tearDown(self):
#         testing.tearDown()

#     def _makeOne(self, request):
#         from max.resources import Root
#         return Root(request)

#     def test_process_new_tweet(self):
#         from maxrules.tasks import processTweet
#         from max.rest.people import addUser
#         request = testing.DummyRequest()
#         root = self._makeOne(request)
#         res = addUser(root, request)
#         import ipdb; ipdb.set_trace( )
#         processTweet.delay('sneridagh', '#Atenea')
