# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header

from functools import partial
from mock import patch
from paste.deploy import loadapp

import os
import unittest
import logging
import tempfile

from logging.handlers import WatchedFileHandler

logger = logging.getLogger('exceptions')
handler = WatchedFileHandler('{}/{}'.format(tempfile.mkdtemp(), 'exceptions.log'))
formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class InfoACLTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(os.path.dirname(__file__))

        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('messages')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)

    def test_execute_maintenance(self):
        """
            Given i'm a regular user
            When i try to execute maintenance endpoints
            Then i get Forbidden Exceptions
        """
        username = 'sheldon'

        self.testapp.post('/admin/maintenance/keywords', headers=oauth2Header(username), status=403)
        self.testapp.post('/admin/maintenance/dates', headers=oauth2Header(username), status=403)
        self.testapp.post('/admin/maintenance/subscriptions', headers=oauth2Header(username), status=403)
        self.testapp.post('/admin/maintenance/conversations', headers=oauth2Header(username), status=403)
        self.testapp.post('/admin/maintenance/users', headers=oauth2Header(username), status=403)
        self.testapp.get('/admin/maintenance/exceptions', headers=oauth2Header(username), status=403)
        self.testapp.get('/admin/maintenance/exceptions/000000', headers=oauth2Header(username), status=403)

    def test_execute_maintenance_as_manager(self):
        """
            Given i'm a Manager
            When i try to execute maintenance endpoints
            Then i succeed
        """
        self.testapp.post('/admin/maintenance/keywords', headers=oauth2Header(test_manager), status=200)
        self.testapp.post('/admin/maintenance/dates', headers=oauth2Header(test_manager), status=200)
        self.testapp.post('/admin/maintenance/subscriptions', headers=oauth2Header(test_manager), status=200)
        self.testapp.post('/admin/maintenance/conversations', headers=oauth2Header(test_manager), status=200)
        self.testapp.post('/admin/maintenance/users', headers=oauth2Header(test_manager), status=200)
        self.testapp.get('/admin/maintenance/exceptions', headers=oauth2Header(test_manager), status=200)
        self.testapp.get('/admin/maintenance/exceptions/000000', headers=oauth2Header(test_manager), status=404)
