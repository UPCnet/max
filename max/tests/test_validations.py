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
        res = self.testapp.post('/contexts', json.dumps(new_context), oauth2Header(test_manager), status=201)
        result = json.loads(res.text)
        self.assertEqual(result.get('twitterUsername', None), create_context_full['twitterUsername'])
        self.assertEqual(result.get('twitterHashtag', None), create_context_full['twitterHashtag'])

    def test_modify_public_context_with_valid_parameters_that_need_formating(self):
        """
            Test validation failure on receiving a invalid twitter username
        """
        from .mockers import create_context_full
        from hashlib import sha1
        res = self.testapp.post('/contexts', json.dumps(create_context_full), oauth2Header(test_manager), status=201)
        url_hash = sha1(create_context_full['url']).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps({"twitterUsername": "@maxupcnet", "twitterHashtag": "#atenea"}), oauth2Header(test_manager), status=200)
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
        res = self.testapp.post('/contexts', json.dumps(bad_context), oauth2Header(test_manager), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'ValidationError')

    def test_add_public_context_with_bad_hashtag(self):
        """
            Test validation failure on receiving a invalid twitter hashtag
        """

        from .mockers import create_context_full
        bad_context = dict(create_context_full)
        bad_context['twitterHashtag'] = '##badhashtag'
        res = self.testapp.post('/contexts', json.dumps(bad_context), oauth2Header(test_manager), status=400)
        result = json.loads(res.text)
        self.assertEqual(result.get('error', None), 'ValidationError')
