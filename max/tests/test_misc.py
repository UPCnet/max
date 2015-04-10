# -*- coding: utf-8 -*-
from max.tests import test_default_security
from max.tests import test_manager
from max.tests.base import MaxTestApp
from max.tests.base import MaxTestBase
from max.tests.base import mock_post
from max.tests.base import oauth2Header
from max.tests.base import mocked_cursor_init
from max.tests.base import FailureCounter
from functools import partial
from mock import patch
from paste.deploy import loadapp

import json
import os
import unittest


def fucked_up_insert():
    """
        This mocked method never really gets executed as it will fail
        on wrong method argument count.
    """
    pass  # pragma: no cover


class FunctionalTests(unittest.TestCase, MaxTestBase):

    def setUp(self):
        self.conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=self.conf_dir)
        self.reset_database(self.app)
        self.app.registry.max_store.security.insert(test_default_security)
        self.patched_post = patch('requests.post', new=partial(mock_post, self))
        self.patched_post.start()
        self.testapp = MaxTestApp(self)

        self.create_user(test_manager)

    # BEGIN TESTS

    def test_root(self):
        """
            Test site root is accessible and returns html
        """
        res = self.testapp.get('/', status=200)
        self.assertEqual(res.content_type, 'text/html')

    def test_bad_test_call_warning(self):
        """
            Test calling a service with missing body parameter, and the authorization as body.
            As this will only probably happen in tests, The error message is targeted so.
        """
        username = 'messi'
        self.create_user(username)
        res = self.testapp.post('/people/%s/activities' % username, oauth2Header(test_manager), status=401)
        self.assertEqual(res.json['error_description'], u'Authorization found in url params, not in request. Check your tests, you may be passing the authentication headers as the request body...')

    @patch('max.models.user.User.insert', fucked_up_insert)
    def test_generic_exception_catching(self):
        """
            Test calling a webservice  moked to force an exception, to test the scavenger
            that formats a beautiful json error messages for uncatched exceptions
        """
        username = 'messi'
        res = self.create_user(username, expect=500)
        self.assertEqual(res.json['error'], 'ServerError')
        self.assertIn('BEGIN EXCEPTION REPORT', res.json['error_description'])
        self.assertIn('END EXCEPTION REPORT', res.json['error_description'])

    def test_bad_body_content_parsing(self):
        """
            Test calling a service with a list on post body, that expects nothing on it
            It should not fail, simply ignore content. Failures would be due a parsing error
            trying to extract actor information from the body.
        """
        username = 'messi'
        self.testapp.post('/people/%s' % username, '[]', oauth2Header(username), status=201)

    def test_post_tunneling_on_delete(self):
        """
            Test that calling a endpoint with DELETE indirectly within a POST
            actually calls the real delete method
        """
        from .mockers import user_status
        username = 'messi'
        self.create_user(username)
        res = self.create_activity(username, user_status)
        activity_id = res.json['id']
        headers = oauth2Header(test_manager)
        headers['X-HTTP-Method-Override'] = 'DELETE'
        self.testapp.post('/activities/{}'.format(activity_id), '', headers, status=204)

    def test_compat_id_match(self):
        """
        """
        username = 'messi'
        self.create_user(username)
        headers = oauth2Header(username)
        headers['X-Max-Compat-ID'] = 'test'
        self.testapp.get('/people', headers=headers, status=200)

    def test_compat_id_mismatch(self):
        """
        """
        username = 'messi'
        self.create_user(username)
        headers = oauth2Header(username)
        headers['X-Max-Compat-ID'] = 'test2'
        self.testapp.get('/people', headers=headers, status=412)

    def test_post_tunneling_on_put(self):
        """
            Test that calling a endpoint with PUT indirectly within a POST
            actually calls the real PUT method
        """
        username = 'messi'
        self.create_user(username)
        headers = oauth2Header(username)
        headers['X-HTTP-Method-Override'] = 'PUT'
        res = self.testapp.post('/people/{}'.format(username), json.dumps({"displayName": "Lionel Messi"}), headers, status=200)
        self.assertEqual(res.request.method, 'PUT')
        self.assertEqual(res.json['displayName'], 'Lionel Messi')

    def test_post_tunneling_on_get(self):
        """
            Test that calling a endpoint with GET indirectly within a POST
            with the headers as post data
            actually calls the real GET method with the "post data headers" injected on real headers
        """
        username = 'messi'
        self.create_user(username)
        params = oauth2Header(username)
        params['X-HTTP-Method-Override'] = 'GET'
        res = self.testapp.post('/people', params, status=200)
        self.assertEqual(res.request.method, 'GET')
        self.assertEqual(res.request.headers['X-Oauth-Username'], params['X-Oauth-Username'])
        self.assertEqual(res.request.headers['X-Oauth-Scope'], params['X-Oauth-Scope'])
        self.assertEqual(res.request.headers['X-Oauth-Token'], params['X-Oauth-Token'])

    def test_image_rotation_180(self):
        from max.utils.image import rotate_image_by_EXIF
        from PIL import Image

        image = Image.open('{}/truita2.jpg'.format(self.conf_dir))
        rotated = rotate_image_by_EXIF(image)
        self.assertNotEqual(image, rotated)

    def test_image_rotation_no_rotation(self):
        from max.utils.image import rotate_image_by_EXIF
        from PIL import Image

        image = Image.open('{}/avatar.png'.format(self.conf_dir))
        rotated = rotate_image_by_EXIF(image)
        self.assertEqual(image, rotated)

    @patch('pymongo.cursor.Cursor.__init__', mocked_cursor_init)
    def test_mongodb_autoreconnect(self):
        """
            Test that if mongodb disconnects once was connected, a autoreconect loop
            will start waiting for mongodb to recover
        """
        #  Make Cursor __init__ fail 3 times with AutoReconnect. Test will show 3 errors similar to
        #  AttributeError: "'Cursor' object has no attribute '_Cursor__killed'" in <bound method Cursor.__del__ of <pymongo.cursor.Cursor object at 0x1072b3410>> ignored
        from max.tests.base import FAILURES
        FAILURES.set(3)

        username = 'messi'
        self.create_user(username)
        self.testapp.get('/people/{}'.format(username), '', headers=oauth2Header(test_manager), status=200)

    @patch('pymongo.cursor.Cursor.__init__', partial(mocked_cursor_init, raise_at_end=True))
    def test_mongodb_autoreconnect_and_crash(self):
        """
            Test that if mongodb disconnects once was connected, a autoreconect loop
            will start waiting for mongodb to recover, And if a different exception raises
            in between, loop will exit and raise the exception
        """
        #  Make Cursor __init__ fail 3 times with AutoReconnect. Test will show 3 errors similar to
        #  AttributeError: "'Cursor' object has no attribute '_Cursor__killed'" in <bound method Cursor.__del__ of <pymongo.cursor.Cursor object at 0x1072b3410>> ignored
        from max.tests.base import FAILURES
        FAILURES.set(3)

        username = 'messi'
        res = self.create_user(username, expect=500)
        self.assertEqual(res.json['error'], 'ServerError')

    def test_request_dumper(self):
        """
            Test request dumper logs requests when activated on
            assigned signal USER1 handler
        """
        import io
        import logging
        import signal
        from max.tweens import request_logger

        # Intercept logger to a variable
        request_logger.setLevel(logging.DEBUG)
        log_capture_string = io.StringIO()
        log_handler = logging.StreamHandler(log_capture_string)
        log_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        log_handler.setFormatter(formatter)
        request_logger.addHandler(log_handler)

        # Retrieve the assigned handler
        handler = signal.getsignal(signal.SIGUSR1)

        handler()  # Enable request dumper
        self.create_user('messi')
        handler()  # Disable request dumper

        # Read lines from captured log
        log_capture_string.seek(0)
        lines = log_capture_string.readlines()
        log_capture_string.close()

        self.assertGreater(len(lines), 2)
        self.assertEqual(lines[0].strip(), 'Enabling request dumper')
        self.assertEqual(lines[-1].strip(), 'Disabling request dumper')

    def test_api_info(self):
        """
            Test that api info endpoint reports all non-info routes
            Test (single route) that expected keys are present on route and method levels
        """
        from max.routes import RESOURCES
        defined_routes = [route_name for route_name in RESOURCES.keys() if not route_name.startswith('info')]

        res = self.testapp.get('/info/api', status=200)

        api_route_names = res.json.keys()
        self.assertIsInstance(res.json, dict)
        self.assertItemsEqual(api_route_names, defined_routes)
        self.assertItemsEqual(res.json['user'].keys(), [u'category', u'name', u'url', u'route', u'filesystem', u'id', u'methods'])
        self.assertItemsEqual(res.json['user']['methods']['GET'].keys(), [u'rest_params', u'query_params', u'documentation', u'description', u'permission'])

    def test_api_info_by_category(self):
        """
        """
        from max.routes import RESOURCES
        defined_categories = list(set([route.get('category') for name, route in RESOURCES.items() if route.get('category')]))
        res = self.testapp.get('/info/api?by_category=1', status=200)

        listed_categories = [category['name'] for category in res.json]

        self.assertIsInstance(res.json, list)
        self.assertItemsEqual(defined_categories, listed_categories)
        self.assertItemsEqual(res.json[0].keys(), [u'name', u'resources', u'id'])

    def test_raw_request_parsing(self):
        """
        """
        from max.exceptions.scavenger import format_raw_request
        from .mockers import mock_request

        res = format_raw_request(mock_request)
        replaced_image = "Content-type: image/png\r\n\r\n<Image data 20496 bytes>\r\n"
        self.assertIn(replaced_image, res)

    def test_raw_request_parsing_error(self):
        """
        """
        from max.exceptions.scavenger import format_raw_request
        from .mockers import mock_request_bad_request

        res = format_raw_request(mock_request_bad_request)
        self.assertIn('*** Error parsing request ***', res)
        self.assertIn('*** End traceback ***', res)

    def test_raw_request_parsing_bad_encoding_error(self):
        """
        """
        from max.exceptions.scavenger import format_raw_request
        from .mockers import mock_request_bad_encoding

        res = format_raw_request(mock_request_bad_encoding)
        self.assertIn('*** Unicode Decode Error parsing request, request trunked at byte 569 ***', res)

    def test_raw_response_parsing(self):
        from max.exceptions.scavenger import format_raw_response
        res = self.testapp.get('/people/test_manager/avatar')
        parsed = format_raw_response(res)
        self.assertIn('<Image data 3909 bytes>', parsed)
