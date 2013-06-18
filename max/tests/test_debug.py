# -*- coding: utf-8 -*-
import os
import unittest
import urllib
from functools import partial

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, MaxTestApp, mock_post
from max.tests import test_manager, test_default_security


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:debug.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

    def test_debugging_mode_does_not_break_normal_app(self):
        """
            Make a simple get in debug mode to test app's normal behaviour
        """
        self.testapp.get('/people', '', status=401)

    def test_make_get_without_oauth(self):
        """
            With oauth2 passtrough and debug api option activated
            Check that we can make a get without getting a 401
        """
        debug_params = dict(
            d='',
            u=test_manager,
        )
        qs = urllib.urlencode(debug_params)
        self.testapp.get('/people?{}'.format(qs), '', {}, status=200)

    def test_make_debug_post_without_user(self):
        """
            With oauth2 passtrough and debug api option activated
            Check that debug mode without a user does not activate
            the method override
        """
        username = 'messi'
        debug_params = dict(
            d='',
            m='post'
        )
        qs = urllib.urlencode(debug_params)
        self.testapp.get('/people/{}?{}'.format(username, qs), '', {}, status=401)

    def test_make_post_as_get(self):
        """
            With oauth2 passtrough and debug api option activated
            Check that we can make a post in a get request
        """
        username = 'messi'
        debug_params = dict(
            d='',
            u=test_manager,
            m='post'
        )
        qs = urllib.urlencode(debug_params)
        self.testapp.get('/people/{}?{}'.format(username, qs), '', {}, status=201)

    def test_make_post_as_get_with_payload(self):
        """
            With oauth2 passtrough and debug api option activated
            Check that we can make a post in a get request
            with json payload as a oneline string
        """

        username = 'messi'
        debug_params = dict(
            d='',
            u=test_manager,
            m='post',
            p='{"displayName":"El messi"}'
        )
        qs = urllib.urlencode(debug_params)
        resp = self.testapp.get('/people/{}?{}'.format(username, qs), '', {}, status=201)
        self.assertEqual(resp.json['displayName'], 'El messi')

    def test_debug_responds_html(self):
        """
            Test that with option 1 in debug mode, we get the output as html
            This is necessary to debug_toolbar to instantiate
        """
        debug_params = dict(
            d='1',
            u=test_manager,
        )
        qs = urllib.urlencode(debug_params)
        res = self.testapp.get('/people?{}'.format(qs), '', {}, status=200)
        self.assertEqual(res.content_type, 'text/html')
        self.assertIn('<html>', res.text)
