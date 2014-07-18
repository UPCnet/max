from max.tests import test_default_security
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header

from functools import partial
from mock import patch
from paste.deploy import loadapp

import json
import os
import shutil
import unittest


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=conf_dir)
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

    def tearDown(self):
        import pyramid.testing
        children_dir = os.listdir(self.app.registry.settings['file_repository'])
        if len(children_dir) > 0:
            shutil.rmtree(self.app.registry.settings['file_repository'] + '/' + children_dir[0])
        pyramid.testing.tearDown()

    # BEGIN TESTS

    def test_create_image_activity(self):
        """
            Given a plain user
            When I post an image activity
            And I am authenticated as myself
            Then the image activity is created correctly
        """
        from .mockers import user_image_activity as activity
        username = 'messi'
        self.create_user(username)
        thefile = open(os.path.join(os.path.dirname(__file__), "avatar.png"), "rb")
        files = [('file', 'avatar.png', thefile.read(), 'image/png')]

        res = self.testapp.post('/people/{}/activities'.format(username), dict(json_data=json.dumps(activity)), oauth2Header(username), upload_files=files, status=201)

        res = self.testapp.get('/people/{}/activities'.format(username), '', oauth2Header(username), status=200)
        response = res.json
        self.assertEqual(response[0]['object'].get('fullURL'), u'/activities/{}/image/full'.format(response[0]['id']))
        self.assertEqual(response[0]['object'].get('thumbURL'), u'/activities/{}/image/thumb'.format(response[0]['id']))

    def test_create_file_activity(self):
        """
            Given a plain user
            When I post a file activity
            And I am authenticated as myself
            Then the file activity is created correctly
        """
        from .mockers import user_file_activity as activity
        username = 'messi'
        self.create_user(username)
        thefile = open(os.path.join(os.path.dirname(__file__), "map.pdf"), "rb")
        files = [('file', 'map.pdf', thefile.read(), 'application/pdf')]

        res = self.testapp.post('/people/{}/activities'.format(username), dict(json_data=json.dumps(activity)), oauth2Header(username), upload_files=files, status=201)

        res = self.testapp.get('/people/{}/activities'.format(username), '', oauth2Header(username), status=200)
        response = res.json
        self.assertEqual(response[0]['object'].get('fullURL'), u'/activities/{}/file/download'.format(response[0]['id']))

    def test_create_image_activity_with_context(self):
        """
            Given a plain user
            When I post an image activity to a context with no uploadURL
            And I am authenticated as myself
            Then the image activity is created correctly
        """
        from .mockers import user_image_activity_with_context as activity
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)

        thefile = open(os.path.join(os.path.dirname(__file__), "avatar.png"), "rb")
        files = [('file', 'avatar.png', thefile.read(), 'image/png')]

        res = self.testapp.post('/people/{}/activities'.format(username), dict(json_data=json.dumps(activity)), oauth2Header(username), upload_files=files, status=201)

        res = self.testapp.get('/people/{}/activities'.format(username), '', oauth2Header(username), status=200)
        response = res.json
        self.assertEqual(response[0]['object'].get('fullURL'), u'/activities/{}/image/full'.format(response[0]['id']))
        self.assertEqual(response[0]['object'].get('thumbURL'), u'/activities/{}/image/thumb'.format(response[0]['id']))

    def test_create_file_activity_with_context(self):
        """
            Given a plain user
            When I post an file activity to a context with no uploadURL
            And I am authenticated as myself
            Then the file activity is created correctly
        """
        from .mockers import user_file_activity_with_context as activity
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)

        thefile = open(os.path.join(os.path.dirname(__file__), "avatar.png"), "rb")
        files = [('file', 'avatar.png', thefile.read(), 'application/pdf')]

        res = self.testapp.post('/people/{}/activities'.format(username), dict(json_data=json.dumps(activity)), oauth2Header(username), upload_files=files, status=201)

        res = self.testapp.get('/people/{}/activities'.format(username), '', oauth2Header(username), status=200)
        response = res.json
        self.assertEqual(response[0]['object'].get('fullURL'), u'/activities/{}/file/download'.format(response[0]['id']))

    def test_create_image_activity_with_context_with_uploadurl(self):
        """
            Given a plain user
            When I post an image activity to a context with uploadURL
            And I am authenticated as myself
            Then the image activity is created correctly
        """
        from .mockers import user_image_activity_with_context_with_uploadurl as activity
        from .mockers import subscribe_context_with_uploadurl, create_context_with_uploadurl
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_with_uploadurl)
        self.admin_subscribe_user_to_context(username, subscribe_context_with_uploadurl)

        thefile = open(os.path.join(os.path.dirname(__file__), "avatar.png"), "rb")
        files = [('file', 'avatar.png', thefile.read(), 'image/png')]

        res = self.testapp.post('/people/{}/activities'.format(username), dict(json_data=json.dumps(activity)), oauth2Header(username), upload_files=files, status=201)

        res = self.testapp.get('/people/{}/activities'.format(username), '', oauth2Header(username), status=200)
        response = res.json
        self.assertEqual(response[0]['object'].get('fullURL'), u'http://localhost:8181/theimage')
        self.assertEqual(response[0]['object'].get('thumbURL'), u'http://localhost:8181/theimage/thumb')

    def test_create_file_activity_with_context_with_uploadurl(self):
        """
            Given a plain user
            When I post an file activity to a context with uploadURL
            And I am authenticated as myself
            Then the file activity is created correctly
        """
        from .mockers import user_file_activity_with_context_with_uploadurl as activity
        from .mockers import subscribe_context_with_uploadurl, create_context_with_uploadurl
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context_with_uploadurl)
        self.admin_subscribe_user_to_context(username, subscribe_context_with_uploadurl)

        thefile = open(os.path.join(os.path.dirname(__file__), "map.pdf"), "rb")
        files = [('file', 'map.pdf', thefile.read(), 'application/pdf')]

        res = self.testapp.post('/people/{}/activities'.format(username), dict(json_data=json.dumps(activity)), oauth2Header(username), upload_files=files, status=201)

        res = self.testapp.get('/people/{}/activities'.format(username), '', oauth2Header(username), status=200)
        response = res.json
        self.assertEqual(response[0]['object'].get('fullURL'), u'http://localhost:8181/theimage')

    def test_post_message_with_image_to_an_already_existing_conversation(self):
        from .mockers import message, message_with_image
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        thefile = open(os.path.join(os.path.dirname(__file__), "avatar.png"), "rb")
        files = [('file', 'avatar.png', thefile.read(), 'image/png')]

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        self.testapp.post('/conversations/%s/messages' % cid, dict(json_data=json.dumps(message_with_image)), oauth2Header(sender), upload_files=files, status=201)

        res = self.testapp.get('/conversations/%s/messages' % cid, "", oauth2Header(sender), status=200)
        result = json.loads(res.text)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].get("contexts", None)[0].get("id", None), cid)
        self.assertEqual(result[0].get("contexts", None)[0].get("objectType", None), "conversation")
        self.assertEqual(result[0].get("objectType", None), "message")
        self.assertEqual(result[1]['object'].get('fullURL'), u'/messages/{}/image/full'.format(result[1]['id']))
        self.assertEqual(result[1]['object'].get('thumbURL'), u'/messages/{}/image/thumb'.format(result[1]['id']))

        full_url = result[1]['object'].get('fullURL')
        res = self.testapp.get(full_url, '', oauth2Header(sender), status=200)

    def test_post_message_with_file_to_an_already_existing_conversation(self):
        from .mockers import message, message_with_file
        sender = 'messi'
        recipient = 'xavi'
        self.create_user(sender)
        self.create_user(recipient)

        thefile = open(os.path.join(os.path.dirname(__file__), "map.pdf"), "rb")
        files = [('file', 'map.pdf', thefile.read(), 'application/pdf')]

        res = self.testapp.post('/conversations', json.dumps(message), oauth2Header(sender), status=201)
        cid = str(res.json['contexts'][0]['id'])
        self.testapp.post('/conversations/%s/messages' % cid, dict(json_data=json.dumps(message_with_file)), oauth2Header(sender), upload_files=files, status=201)

        res = self.testapp.get('/conversations/%s/messages' % cid, "", oauth2Header(sender), status=200)
        result = json.loads(res.text)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].get("contexts", None)[0].get("id", None), cid)
        self.assertEqual(result[0].get("contexts", None)[0].get("objectType", None), "conversation")
        self.assertEqual(result[0].get("objectType", None), "message")
        self.assertEqual(result[1]['object'].get('fullURL'), u'/messages/{}/file/download'.format(result[1]['id']))

    def test_get_image_activity_file_with_context(self):
        """
            Given a plain user
            When I post an image activity to a context with no uploadURL
            And I am authenticated as myself
            Then the image activity is created correctly
        """
        from .mockers import user_image_activity_with_context as activity
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)

        thefile = open(os.path.join(os.path.dirname(__file__), "avatar.png"), "rb")
        files = [('file', 'avatar.png', thefile.read(), 'image/png')]

        res = self.testapp.post('/people/{}/activities'.format(username), dict(json_data=json.dumps(activity)), oauth2Header(username), upload_files=files, status=201)

        res = self.testapp.get('/people/{}/activities'.format(username), '', oauth2Header(username), status=200)
        response = res.json

        res = self.testapp.get('/activities/{}/image/full'.format(response[0]['id']), '', oauth2Header(username), status=200)
        self.assertEqual(len(res.body), 20492)
        self.assertEqual(res.content_type, u'image/png')

    def test_get_file_activity_file_with_context(self):
        """
            Given a plain user
            When I post an file activity to a context with no uploadURL
            And I am authenticated as myself
            Then the file activity is created correctly
            And I can retrieve it with the endpoint
        """
        from .mockers import user_file_activity_with_context as activity
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)

        thefile = open(os.path.join(os.path.dirname(__file__), "map.pdf"), "rb")
        files = [('file', 'map.pdf', thefile.read(), 'application/pdf')]

        res = self.testapp.post('/people/{}/activities'.format(username), dict(json_data=json.dumps(activity)), oauth2Header(username), upload_files=files, status=201)

        res = self.testapp.get('/people/{}/activities'.format(username), '', oauth2Header(username), status=200)
        response = res.json

        res = self.testapp.get('/activities/{}/file/download'.format(response[0]['id']), '', oauth2Header(username), status=200)

        self.assertEqual(len(res.body), 34981)
        self.assertEqual(res.content_type, u'application/pdf')

    def test_get_file_activity_file_with_context_not_allowed_user(self):
        """
            Given a file activity created by me in a context
            When an user non subscribed to this context tries to retrieve it
            Then the user cannot acces the file activity
        """
        from .mockers import user_file_activity_with_context as activity
        from .mockers import subscribe_context, create_context
        username = 'messi'
        username2 = 'thor'
        self.create_user(username)
        self.create_user(username2)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)

        thefile = open(os.path.join(os.path.dirname(__file__), "map.pdf"), "rb")
        files = [('file', 'map.pdf', thefile.read(), 'application/pdf')]

        res = self.testapp.post('/people/{}/activities'.format(username), dict(json_data=json.dumps(activity)), oauth2Header(username), upload_files=files, status=201)

        res = self.testapp.get('/people/{}/activities'.format(username), '', oauth2Header(username), status=200)
        response = res.json

        res = self.testapp.get('/activities/{}/file/download'.format(response[0]['id']), '', oauth2Header(username2), status=401)

    def test_get_thumb_image_activity_file_with_context(self):
        """
            Given a plain user
            When I post an image activity to a context with no uploadURL
            And I am authenticated as myself
            Then the image activity is created correctly
        """
        from .mockers import user_image_activity_with_context as activity
        from .mockers import subscribe_context, create_context
        username = 'messi'
        self.create_user(username)
        self.create_context(create_context)
        self.admin_subscribe_user_to_context(username, subscribe_context)

        thefile = open(os.path.join(os.path.dirname(__file__), "avatar.png"), "rb")
        files = [('file', 'avatar.png', thefile.read(), 'image/png')]

        res = self.testapp.post('/people/{}/activities'.format(username), dict(json_data=json.dumps(activity)), oauth2Header(username), upload_files=files, status=201)

        res = self.testapp.get('/people/{}/activities'.format(username), '', oauth2Header(username), status=200)
        response = res.json

        res = self.testapp.get('/activities/{}/image/thumb'.format(response[0]['id']), '', oauth2Header(username), status=200)

        # Give a margin of size of 10 bytes, sometimes readed image
        # size differs by two bytes, who knows why ...
        self.assertLessEqual(abs(len(res.body) - 2966), 10)

        self.assertEqual(res.content_type, u'image/jpeg')
