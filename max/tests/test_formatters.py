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
        self.app.registry.max_store.security.insert(test_default_security)
        self.testapp = MaxTestApp(self)

    # BEGIN TESTS

    def test_create_activity_strip_tags(self):
        """ doctest .. http:post:: /people/{username}/activities """
        from .mockers import user_status
        username = 'messi'
        activity = dict(user_status)  # Make a copy
        self.create_user(username)
        activity['object']['content'] = '<p>A <strong>text</strong> A</p>'
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(username), status=201)
        self.assertEqual(res.json['object']['content'], 'A <strong>text</strong> A')
