# -*- coding: utf-8 -*-
import os
import json
import unittest
from hashlib import sha1

from mock import patch
from paste.deploy import loadapp

from max.tests.base import MaxTestBase, oauth2Header
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
        from webtest import TestApp
        self.testapp = TestApp(self.app)

    # BEGIN TESTS

    def test_subcribe_to_restricted_context_as_plain_user(self):
        from .mockers import create_context
        from .mockers import subscribe_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context, permissions=dict(read='public', write='restricted', join='restricted', invite='restricted'))
        self.subscribe_user_to_context(username, subscribe_context, auth=username, expect=401)
