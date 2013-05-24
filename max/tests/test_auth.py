# -*- coding: utf-8 -*-
"""
    Authentication tests

    This tests doesn't have the requests.post patched,
    so real request to oauth are done

"""
import os
import unittest

from paste.deploy import loadapp
from mock import patch

from max.tests.base import MaxTestBase, MaxTestApp, oauth2Header
from max.tests import test_default_security


class mock_requests_obj(object):

    def __init__(self, *args, **kwargs):
        self.text = kwargs['text']
        self.status_code = kwargs['status_code']


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
        self.patched_post = patch('requests.post', new=self.mock_post)
        self.patched_post.start()

    def mock_post(self, *args, **kwargs):  # pragma: no cover
        if args[0].endswith('checktoken'):
            return mock_requests_obj(text='', status_code=403)
        else:
            return mock_requests_obj(text='', status_code=200)

    # BEGIN TESTS

    def test_invalid_token(self):
        username = 'messi'
        res = self.create_user(username, expect=401)
        self.assertEqual(res.json['error_description'], 'Invalid token.')
