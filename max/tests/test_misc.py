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

    def test_bad_test_call_warning(self):
        """
            Test calling a service with missing body parameter, and the authorization as body.
            As this will only probably happen in tests, The error message is targeted so.
        """
        username = 'messi'
        res = self.testapp.post('/people/%s' % username, oauth2Header(test_manager), status=401)
        self.assertEqual(res.json['error_description'], u'Authorization found in url params, not in request. Check your tests, you may be passing the authentication headers as the request body...')

