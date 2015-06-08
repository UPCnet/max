# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import http_mock_bitly
from max.tests.base import mock_post
from max.tests.base import oauth2Header
from max.tests import test_manager

from functools import partial
from mock import patch
from paste.deploy import loadapp

import httpretty
import json
import os
import unittest


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.reset_database(self.app)
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)

    def tearDown(self):
        self.patched_post.stop()

    # BEGIN TESTS

    def test_create_activity_strip_tags(self):
        """ doctest .. http:post:: /people/{username}/activities """
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(user_status), oauth2Header(username), status=201)
        self.assertEqual(res.json['object']['content'], u"[A] Testejant la creació d'un canvi d'estatus")

    def test_post_comment_strip_tags(self):
        """ doctest .. http:post:: /activities/{activity}/comments """
        from .mockers import user_status, user_comment
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)
        activity = self.create_activity(username, user_status)
        activity = activity.json
        res = self.testapp.post('/activities/%s/comments' % str(activity.get('id')), json.dumps(user_comment), oauth2Header(username), status=201)
        self.assertEqual(res.json['object']['content'], u"[C] Testejant un comentari nou a una activitat")

    def test_post_message_to_conversation_strip_tags(self):
        """ doctest .. http:post:: /conversations """
        from .mockers import message_with_tags
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        res = self.testapp.post('/conversations', json.dumps(message_with_tags), oauth2Header(sender), status=201)
        self.assertEqual(res.json['object']['content'], u'A <strong>text</strong> A')

    def test_post_activity_shortens_url(self):
        """  """
        from .mockers import user_status_with_url
        username = 'messi'
        self.create_user(username)
        res = self.create_activity(username, user_status_with_url)
        self.assertIn('bit.ly', res.json['object']['content'],)

    @httpretty.activate
    def test_url_shortened_bitly_failure(self):
        from max.utils.formatting import shortenURL

        http_mock_bitly(status=500)
        url = 'http://example.com'
        newurl = shortenURL(url)
        self.assertEqual(url, newurl)

    @httpretty.activate
    def test_url_shortened_parsing_failure(self):
        from max.utils.formatting import shortenURL

        http_mock_bitly(status=500, body="invalid json")
        url = 'http://example.com'
        newurl = shortenURL(url)
        self.assertEqual(url, newurl)

    @httpretty.activate
    def test_url_shortened(self):
        from max.utils.formatting import shortenURL

        http_mock_bitly()
        url = 'http://example.com'
        newurl = shortenURL(url)
        self.assertEqual(newurl, "http://shortened.url")

    @httpretty.activate
    def test_url_secure_shortened(self):
        from max.utils.formatting import shortenURL

        http_mock_bitly()
        url = 'http://example.com'
        newurl = shortenURL(url, secure=True)
        self.assertEqual(newurl, "https://shortened.url")
