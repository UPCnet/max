# -*- coding: utf-8 -*-
import os
import json
import unittest

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header
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
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('messages')

        self.app.registry.max_store.security.insert(test_default_security)
        self.testapp = MaxTestApp(self)

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
