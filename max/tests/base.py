# -*- coding: utf-8 -*-
from max.tests import test_manager
from max.utils.dicts import deepcopy
from max.utils.image import get_avatar_folder

from PIL import Image
from io import BytesIO
from pymongo.cursor import Cursor
from pymongo.errors import AutoReconnect
from urllib import urlencode

import httpretty
import json
import os
import pymongo
import re
import requests
import shutil
import tweepy


MOCK_TOKEN = "jfa1sDF2SDF234"

# Copy of original patched methods
requests_get = requests.get
requests_post = requests.post
original_cursor_init = Cursor.__init__


class FailureCounter(object):
    def __init__(self, count):
        self.count = count

    def dec(self):
        self.count -= 1

    def set(self, count):
        self.count = count


FAILURES = FailureCounter(3)


def http_mock_twitter_user_image(image, status=200):
    httpretty.register_uri(
        httpretty.GET, "https://pbs.twimg.com/profile_images/1901828730/logo_MAX_color_normal.png",
        body=open(image, "rb").read(),
        status=status,
        content_type="image/png"
    )


def http_mock_bitly(status=200, body=None):
    body = '{"status_code": %s, "data": {"url": "http://shortened.url"}}' % status if body is None else body
    httpretty.register_uri(
        httpretty.GET, re.compile("http://api.bitly.com"),
        body=body,
        status=status,
        content_type="application/json"
    )


class MockTweepyAPI(object):
    def __init__(self, auth, fail=False, provide_image=True):
        self.fail = fail
        self.provide_image = provide_image

    def verify_credentials(self, *args, **kwargs):
        if self.fail:
            raise Exception('Simulated Twitter Failure')
        return True

    def get_user(self, username):
        user = tweepy.models.User()
        if self.provide_image:
            user.profile_image_url_https = 'https://pbs.twimg.com/profile_images/1901828730/logo_MAX_color_normal.png'
        user.id_str = '526326641'
        return user


def mocked_cursor_init(self, *args, **kwargs):
    raise_at_end = kwargs.pop('raise_at_end', False)
    if FAILURES.count == 0:
        return original_cursor_init(self, *args, **kwargs)
    elif FAILURES.count == 1 and raise_at_end:
        FAILURES.dec()
        raise Exception('Raised on AutoReconnect loop')

    FAILURES.dec()
    raise AutoReconnect('Mocked AutoReconnect failure')


def impersonate_payload(source, username):
    """
        Adds an actor to a payload, to impersonate it
    """
    base = deepcopy(source)
    base['actor'] = {
        'objectType': 'person',
        'username': username
    }
    return base


class mock_requests_obj(object):

    def __init__(self, *args, **kwargs):
        if kwargs.get('text', None) is not None:
            self.text = kwargs['text']
        if kwargs.get('content', None) is not None: # pragma: no cover
            self.content = kwargs['content']
        self.status_code = kwargs['status_code']


def mock_post(self, url, *args, **kwargs):  # pragma: no cover
    # Return OK to any post request targeted to 'checktoken', with the mock token
    if url.endswith('checktoken'):
        token = kwargs.get('data', {}).get('access_token')
        status_code = 200 if token == MOCK_TOKEN else 401
        return mock_requests_obj(text='', status_code=status_code)
    elif '/people/messi/activities' in url:
        # Fake the requests.post thorough the self.testapp instance, and test result later in test
        res = self.testapp.post('/people/%s/activities' % 'messi', args[0], oauth2Header(test_manager), status=201)
        return mock_requests_obj(text=res.text, status_code=201)
    elif '/contexts/90c8f28a7867fbad7a2359c6427ae8798a37ff07/activities' in url:
        # Fake the requests.post thorough the self.testapp instance, and test result later in test
        res = self.testapp.post('/contexts/%s/activities' % '90c8f28a7867fbad7a2359c6427ae8798a37ff07', args[1], oauth2Header(test_manager), status=201)
        return mock_requests_obj(text=res.text, status_code=201)
    elif url.endswith('upload'):
        return mock_requests_obj(text='{"uploadURL": "http://localhost:8181/theimage", "thumbURL": "http://localhost:8181/theimage/thumb"}', status_code=201)
    else:
        # Proceed with unpatched requests post
        return requests_post(*args, **kwargs)


def mock_get(self, *args, **kwargs):  # pragma: no cover
    # if args[0].lower() == 'http://api.twitter.com/1/users/show.json?screen_name=maxupcnet':
    #     result = '{"id_str":"526326641", "profile_image_url_https": "https://si0.twimg.com/profile_images/1901828730/logo_MAX_color_normal.png"}'
    #     return mock_requests_obj(text=result, status_code=200)
    # elif args[0].endswith('logo_MAX_color_normal.png'):
    #     request = get_current_request()
    #     if request.headers.get('SIMULATE_TWITTER_FAIL', False):
    #         return mock_requests_obj(text='', status_code=500)
    #     else:
    #         return mock_requests_obj(content=image, status_code=200)
    # else:
    #     # Proceed with unpatched requests get
        return requests_get(*args, **kwargs)


def oauth2Header(username, token=MOCK_TOKEN, scope="widgetcli"):
    return {
        "X-Oauth-Token": token,
        "X-Oauth-Username": username,
        "X-Oauth-Scope": scope}


class MaxTestApp(object):

    def __init__(self, testcase):
        from webtest import TestApp
        self.testcase = testcase
        self.testapp = TestApp(testcase.app)

    def get(self, *args, **kwargs):
        return self.call_testapp('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.call_testapp('post', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.call_testapp('put', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.call_testapp('delete', *args, **kwargs)

    def head(self, *args, **kwargs):
        return self.call_testapp('head', *args, **kwargs)

    def call_testapp(self, method, *args, **kwargs):

        status = kwargs.get('status', None)
        testapp_method = getattr(self.testapp, method)
        kwargs['expect_errors'] = True
        res = testapp_method(*args, **kwargs)
        if status is not None:
            message = "Response status is {},  we're expecting {}. ".format(res.status_int, status)
            # Identify whem response  contains a json formatted error
            if hasattr(res, 'json'):
                if 'error' in getattr(res, 'json', []):
                    message += '\nRaised {error}: "{error_description}"'.format(**res.json)
            # Identify errors without json
            elif res.status_int != status:  # pragma: no cover
                print res.body
                # Print a alert to avoid going mad again debugging why a
                # error response has no body, because was a HEAD ...
                if res.request.method == 'HEAD':
                    message += "\n\n  !!! WARNING:  Response has no body beacause is a HEAD request. !!!"

            self.testcase.assertEqual(status, res.status_int, message)
        return res


class MaxAvatarsTestBase(object):

    def setUp(self):
        self.avatar_folder = self.app.registry.settings['avatar_folder']

        if not os.path.exists(self.avatar_folder):  # pragma: no cover
            os.mkdir(self.avatar_folder)

        # Generate default avatar images
        shutil.copyfile('{}/missing.png'.format(self.conf_dir), '{}/missing.png'.format(self.avatar_folder))
        shutil.copyfile('{}/missing.png'.format(self.conf_dir), '{}/missing-people.png'.format(self.avatar_folder))
        shutil.copyfile('{}/missing.png'.format(self.conf_dir), '{}/missing-context.png'.format(self.avatar_folder))
        shutil.copyfile('{}/missing.png'.format(self.conf_dir), '{}/missing-conversation.png'.format(self.avatar_folder))
        shutil.copyfile('{}/missing.png'.format(self.conf_dir), '{}/missing-people-large.png'.format(self.avatar_folder))

    def tearDown(self):
        shutil.rmtree(self.avatar_folder)

    def get_image_dimensions_from(self, response):
        """
            Returns the (width, height) of an image found in a request response.
        """
        return Image.open(BytesIO(response.body)).size

    def get_context_avatar_modification_time(self, context):
        """
            Returns the (width, height) of an image for a especifi user, located
            in the designated folder for that user.
        """
        avatar_folder = get_avatar_folder(self.avatar_folder, 'contexts', context)
        filename = '{}/{}'.format(avatar_folder, context)
        return os.path.getmtime(filename)

    def rewind_context_avatar_mod_time(self, context, hours):
        """
            Changes the contex's avatar file modifcation time x hours back in time
        """
        avatar_folder = get_avatar_folder(self.avatar_folder, 'contexts', context)
        filename = '{}/{}'.format(avatar_folder, context)
        modification_time = os.path.getmtime(filename)
        new_time = modification_time - (hours * 60 * 60)
        os.utime(filename, (new_time, new_time))

    def get_user_avatar_dimensions(self, username, size=''):
        """
            Returns the (width, height) of an image for a especifi user, located
            in the designated folder for that user.
        """
        avatar_folder = get_avatar_folder(self.avatar_folder, 'people', username, size=size)
        return Image.open('{}/{}'.format(avatar_folder, username)).size

    def upload_user_avatar(self, username, filename):
        """
            Uploads the file specified in filename, to become the avatar for
            username.
        """
        avatar_file = open(os.path.join(self.conf_dir, filename), "rb")
        files = [('image', filename, avatar_file.read(), 'image/png')]
        self.testapp.post('/people/{}/avatar'.format(username), '', headers=oauth2Header(username), upload_files=files, status=201)


class MaxTestBase(object):

    def __init__(self, testapp):  # pragma: no cover
        self.testapp = testapp

    def reset_database(self, app):
        self.app.registry.max_store.drop_collection('users')
        self.app.registry.max_store.drop_collection('activity')
        self.app.registry.max_store.drop_collection('contexts')
        self.app.registry.max_store.drop_collection('conversations')
        self.app.registry.max_store.drop_collection('messages')
        self.app.registry.max_store.drop_collection('security')
        self.app.registry.max_store.drop_collection('tokens')
        self.app.registry.max_store.drop_collection('cloudapis')

    def assertFileExists(self, path):
        self.assertTrue(os.path.exists(path))

    def assertFileNotExists(self, path):
        self.assertFalse(os.path.exists(path))

    def create_user(self, username, qs_params={}, expect=201, creator=test_manager, **kwargs):
        payload = {'username': username}
        for key, value in kwargs.items():
            payload[key] = value

        qs = '?{}'.format(urlencode(qs_params)) if qs_params else ''
        res = self.testapp.post('/people%s' % (qs), json.dumps(payload), oauth2Header(creator), status=expect)
        return res

    def modify_user(self, username, properties):
        res = self.testapp.put('/people/%s' % username, json.dumps(properties), oauth2Header(username))
        return res

    def create_activity(self, username, activity, oauth_username=None, expect=201, note=None):
        oauth_username = oauth_username is not None and oauth_username or username
        new_activity = deepcopy(activity)
        if note is not None:
            new_activity['object']['content'] = note

        res = self.testapp.post('/people/%s/activities' % username, json.dumps(new_activity), oauth2Header(oauth_username), status=expect)
        return res

    def comment_activity(self, username, activity_id, comment, expect=201):
        res = self.testapp.post('/activities/%s/comments' % str(activity_id), json.dumps(comment), oauth2Header(username), status=expect)
        return res

    def delete_activity_comment(self, username, activity_id, comment_id, expect=204):
        res = self.testapp.delete('/activities/%s/comments/%s' % (str(activity_id), comment_id), '', oauth2Header(username), status=expect)
        return res

    def like_activity(self, username, activity_id, expect=201):
        res = self.testapp.post('/activities/%s/likes' % activity_id, '', oauth2Header(username), status=expect)
        return res

    def flag_activity(self, username, activity_id, expect=201):
        res = self.testapp.post('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=expect)
        return res

    def unflag_activity(self, username, activity_id, expect=204):
        res = self.testapp.delete('/activities/%s/flag' % activity_id, '', oauth2Header(username), status=expect)
        return res

    def favorite_activity(self, username, activity_id, expect=201):
        res = self.testapp.post('/activities/%s/favorites' % activity_id, '', oauth2Header(username), status=expect)
        return res

    def create_context(self, context, permissions={}, expect=201, owner=None):
        default_permissions = dict(read='public', write='public', subscribe='public', invite='subscribed')
        new_context = dict(context)
        if 'permissions' not in new_context:
            new_context['permissions'] = default_permissions
        new_context['permissions'].update(permissions)

        if owner is not None:
            new_context['owner'] = owner
        res = self.testapp.post('/contexts', json.dumps(new_context), oauth2Header(test_manager), status=expect)
        return res

    def modify_context(self, context, properties):
        from hashlib import sha1
        url_hash = sha1(context).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps(properties), oauth2Header(test_manager), status=200)
        return res

    def revoke_permission(self, chash, username, permission, expect=201):
        res = self.testapp.delete('/contexts/%s/permissions/%s/%s?permanent=1' % (chash, username, permission), "", oauth2Header(test_manager), status=expect)
        return res

    def grant_permission(self, chash, username, permission, expect=201):
        res = self.testapp.put('/contexts/%s/permissions/%s/%s?permanent=1' % (chash, username, permission), "", oauth2Header(test_manager), status=expect)
        return res

    def admin_subscribe_user_to_context(self, username, context, expect=201):
        """
            Subscribes an user to a context as a manager user
        """
        res = self.testapp.post('/people/%s/subscriptions' % username, json.dumps(context), oauth2Header(test_manager), status=expect)
        return res

    def user_subscribe_user_to_context(self, username, context, auth_user=None, expect=201):
        """
            Subscribes an user to a context as himself
        """
        auth_user = username if auth_user is None else auth_user
        res = self.testapp.post('/people/%s/subscriptions' % username, json.dumps(context), oauth2Header(auth_user), status=expect)
        return res

    def admin_unsubscribe_user_from_context(self, username, chash, expect=204):
        """
            UnSubscribes an user to a context as himself
        """
        res = self.testapp.delete('/contexts/%s/subscriptions/%s' % (chash, username), {}, oauth2Header(test_manager), status=expect)
        return res

    def user_unsubscribe_user_from_context(self, username, chash, auth_user=None, expect=204):
        """
            UnSubscribes an user to a context as himself
        """
        auth_user = username if auth_user is None else auth_user
        res = self.testapp.delete('/contexts/%s/subscriptions/%s' % (chash, username), {}, oauth2Header(auth_user), status=expect)
        return res

    def exec_mongo_query(self, collection, method, query, action={}):
        conn = pymongo.MongoClient('mongodb://localhost:27017')
        db = conn['tests']
        mongo_method = getattr(db[collection], method)
        if method == 'find':
            return [a for a in mongo_method(query)]
        else:
            return mongo_method(query, action)


