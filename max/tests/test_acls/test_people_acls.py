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

import json
import os
import unittest


class PeopleACLTests(unittest.TestCase, MaxTestBase):

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

    # Add people tests

    def test_create_person_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to create a person
            I succeed
        """
        username = 'sheldon'
        self.testapp.post('/people', json.dumps({"username": username}), headers=oauth2Header(test_manager), status=201)

    def test_create_person_as_non_manager(self):
        """
            Given i'm user that doesn't have the Manager role
            When i try to create a person
            I get a Forbidden exception
        """
        username = 'sheldon'
        other = 'penny'
        self.testapp.post('/people', json.dumps({"username": other}), headers=oauth2Header(username), status=403)

    def test_create_person_as_oneself(self):
        """
            Given i'm user that doesn't have the Manager role
            When i try to create a person
            I succeed
        """
        username = 'sheldon'
        self.testapp.post('/people', json.dumps({"username": username}), headers=oauth2Header(username), status=201)

    # View profile tests

    def test_get_person_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to view a user profile
            I succeed
        """
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        self.testapp.get('/people/{}'.format(username), "", headers=oauth2Header(test_manager), status=200)

    def test_get_person_as_non_manager(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to view a user profile
            I succeed
        """
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        self.testapp.get('/people/{}'.format(test_manager), "", headers=oauth2Header(username), status=200)

    # Get all people

    def test_get_all_people_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to get all people
            I succeed
        """
        self.create_user(test_manager)
        self.testapp.get('/people', "", headers=oauth2Header(test_manager), status=200)

    def test_get_all_people_as_non_manager(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to get a visible people listing
            I suceed
        """
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        self.testapp.get('/people', "", headers=oauth2Header(username), status=200)

    # Modify user tests

    def test_modify_person_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to modify a user profile
            I succeed
        """
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        self.testapp.put('/people/{}'.format(username), "", headers=oauth2Header(test_manager), status=200)

    def test_modify_person_as_non_manager_neither_owner(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to modify a user profile
            And that person is not me
            I get a Forbidden Exception
        """
        username = 'sheldon'
        other = 'penny'

        self.create_user(test_manager)
        self.create_user(username)
        self.create_user(other)
        self.testapp.put('/people/{}'.format(other), "", headers=oauth2Header(username), status=403)

    def test_modify_person_as_owner(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to modify my own profile
            I succeed
        """
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        self.testapp.put('/people/{}'.format(username), "", headers=oauth2Header(username), status=200)

    # Delete user tests

    def test_delete_person_as_manager(self):
        """
            Given i'm a user that has the Manager role
            When i try to delete a user
            I succeed
        """
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        self.testapp.delete('/people/{}'.format(username), headers=oauth2Header(test_manager), status=204)

    def test_delete_person_as_non_manager_neither_owner(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to delete a user
            I get a Forbidden Exception
        """
        username = 'sheldon'
        other = 'penny'

        self.create_user(test_manager)
        self.create_user(username)
        self.create_user(other)
        self.testapp.delete('/people/{}'.format(other), headers=oauth2Header(username), status=403)

    def test_delete_person_as_owner(self):
        """
            Given i'm a user that doesn't have the Manager role
            When i try to delete myself
            I get a Forbidden Exception
        """
        username = 'sheldon'

        self.create_user(test_manager)
        self.create_user(username)
        self.testapp.delete('/people/{}'.format(username), headers=oauth2Header(username), status=403)
