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

    def test_user_activities_stats(self):
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)

        for i in range(11):
            self.create_activity(username, user_status)
        res = self.testapp.get('/people/%s/activities' % username, '', oauth2Header(username), status=200)
        self.assertEqual(res.json.get('totalItems'), 10)
        res = self.testapp.head('/people/%s/activities' % username, oauth2Header(username), status=200)
        self.assertEqual(res.headers.get('X-totalItems'), '11')
