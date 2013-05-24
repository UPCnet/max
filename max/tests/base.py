import json
import base64

from max.tests import test_manager


def oauth2Header(username):
    return {"X-Oauth-Token": "jfa1sDF2SDF234", "X-Oauth-Username": username, "X-Oauth-Scope": "widgetcli"}


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
            if hasattr(res, 'json'):
                if 'error' in getattr(res, 'json', []):
                    message += '\nRaised {error}: "{error_description}"'.format(**res.json)
            self.testcase.assertEqual(status, res.status_int, message)
        return res


class MaxTestBase(object):

    def __init__(self, testapp):
        self.testapp = testapp

    def create_user(self, username, **kwargs):
        payload = {}
        for key, value in kwargs.items():
            payload[key] = value
        res = self.testapp.post('/people/%s' % username, json.dumps(payload), oauth2Header(test_manager), status=201)
        return res

    def modify_user(self, username, properties):
        res = self.testapp.put('/people/%s' % username, json.dumps(properties), oauth2Header(username))
        return res

    def create_activity(self, username, activity, oauth_username=None, expect=201):
        oauth_username = oauth_username is not None and oauth_username or username
        res = self.testapp.post('/people/%s/activities' % username, json.dumps(activity), oauth2Header(oauth_username), status=expect)
        return res

    def create_context(self, context, permissions=None, expect=201):
        default_permissions = dict(read='public', write='public', subscribe='public', invite='subscribed')
        new_context = dict(context)
        if 'permissions' not in new_context:
            new_context['permissions'] = default_permissions
        if permissions:
            new_context['permissions'].update(permissions)
        res = self.testapp.post('/contexts', json.dumps(new_context), oauth2Header(test_manager), status=expect)
        return res

    def modify_context(self, context, properties):
        from hashlib import sha1
        url_hash = sha1(context).hexdigest()
        res = self.testapp.put('/contexts/%s' % url_hash, json.dumps(properties), oauth2Header(test_manager), status=200)
        return res

    def admin_subscribe_user_to_context(self, username, context, expect=201,):
        """
            Subscribes an user to a context as a manager user
        """
        res = self.testapp.post('/people/%s/subscriptions' % username, json.dumps(context), oauth2Header(test_manager), status=expect)
        return res

    def user_subscribe_user_to_context(self, username, context, expect=201,):
        """
            Subscribes an user to a context as himself
        """
        res = self.testapp.post('/people/%s/subscriptions' % username, json.dumps(context), oauth2Header(username), status=expect)
        return res

    def admin_unsubscribe_user_from_context(self, username, chash, expect=204):
        """
            UnSubscribes an user to a context as himself
        """
        res = self.testapp.delete('/people/%s/subscriptions/%s' % (username, chash), {}, oauth2Header(test_manager), status=expect)
        return res

    def user_unsubscribe_user_from_context(self, username, chash, expect=204):
        """
            UnSubscribes an user to a context as himself
        """
        res = self.testapp.delete('/people/%s/subscriptions/%s' % (username, chash), {}, oauth2Header(username), status=expect)
        return res
