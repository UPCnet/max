import unittest
import os
from paste.deploy import loadapp
import base64
import json

from mock import patch


class mock_post(object):

    def __init__(self, *args, **kwargs):
        pass

    text = ""
    status_code = 200


@patch('requests.post', new=mock_post)
class FunctionalTests(unittest.TestCase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        from webtest import TestApp
        self.testapp = TestApp(self.app)

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

    def subscribe_user_to_context(self, username, context, expect=201):
        res = self.testapp.post('/people/%s/subscriptions' % username, json.dumps(context), basicAuthHeader('operations', 'operations'), status=expect)
        return res

    # BEGIN TESTS

    def test_add_public_context_with_valid_parameters_that_needs_formating(self):
        """
            Test formatters acting correctly by testing the extraction of the "@" and "#"
            on receiving a twitter @username and #hashtag containing extra chars (@,# and trailing/leading whitespace)
        """
        from .mockers import create_context_full
        new_context = dict(create_context_full)
        new_context['twitterUsername'] = '@%s ' % create_context_full['twitterUsername']
        new_context['twitterHashtag'] = '  #%s' % create_context_full['twitterHashtag']
        res = self.testapp.post('/contexts', json.dumps(new_context), basicAuthHeader('operations', 'operations'), status=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('twitterUsername', None), create_context_full['twitterUsername'])
        self.assertEqual(result.get('twitterHashtag', None), create_context_full['twitterHashtag'])

    def test_modify_public_context_with_valid_parameters_that_need_formating(self):
        """
            Test validation failure on receiving a invalid twitter username
        """
        from .mockers import create_context_full
        from hashlib import sha1
        res = self.testapp.post('/contexts', json.dumps(create_context_full), basicAuthHeader('operations', 'operations'), status=201)
        url_hash = sha1(create_context_full['object']['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterUsername": "@maxupcnet","twitterHashtag": "#atenea"}), basicAuthHeader('operations', 'operations'), status=200)
        result = json.loads(res.text)
        self.assertEqual(result.get('twitterUsername', None), 'maxupcnet')
        self.assertEqual(result.get('twitterHashtag', None), 'atenea')


    def test_add_public_context_with_bad_twitter_username(self):
        """
            Test validation failure on receiving a invalid twitter username
        """
        from .mockers import create_context_full
        bad_context = dict(create_context_full)
        bad_context['twitterUsername'] = '@@badusername'
        res = self.testapp.post('/contexts', json.dumps(bad_context), basicAuthHeader('operations', 'operations'), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'ValidationError')


    def test_add_public_context_with_bad_hashtag(self):
        """
            Test validation failure on receiving a invalid twitter hashtag
        """

        from .mockers import create_context_full
        bad_context = dict(create_context_full)
        bad_context['twitterHashtag'] = '##badhashtag'
        res = self.testapp.post('/contexts', json.dumps(bad_context), basicAuthHeader('operations', 'operations'), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'ValidationError')


def basicAuthHeader(username, password):
    base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
    return dict(Authorization="Basic %s" % base64string)


def oauth2Header(username):
    return {"X-Oauth-Token": "jfa1sDF2SDF234", "X-Oauth-Username": username, "X-Oauth-Scope": "widgetcli"}
