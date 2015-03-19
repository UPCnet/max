# -*- coding: utf-8 -*-
import re
import json
from hashlib import sha1

people_resource_matcher = re.compile(r'/people/([^\/]+)$').search
people_subscriptions_resource_matcher = re.compile(r'/people/([^\/]+)/subscriptions$').search


def fix_deprecated_create_user(request, match):
    """
        Adapts the deprecated way to create an user.

        Requests matching:

            POST /people/{user}

        will be transformed into:

            POST /people

        Username will be injected into the json body
        overwriting any username specified, but preserving
        any other user attribute
    """
    username = match.groups()[0]
    try:
        replacement_body = json.loads(request.body)
    except:
        replacement_body = {}
    replacement_body['username'] = username
    request.body = json.dumps(replacement_body)
    request.path_info = '/people'


def fix_deprecated_subscribe_user(request, match):
    """
        Adapts the deprecated way to subscribe an user to a context

        Requests matching:

            POST /people/{user}/subscriptions

        will be transformed into:

            POST /contexts/{hash}/subscriptions

        Hash will be extracted from the url on the json body,
        and a actor parameter will be injected into the json body,
        using username found in the url
    """
    username = match.groups()[0]
    try:
        original_body = json.loads(request.body)
    except:
        original_body = {}

    object_url = original_body.get('object', {}).get('url', None)
    url_hash = sha1(object_url).hexdigest() if object_url else ''
    new_path = '/contexts/{}/subscriptions'.format(url_hash)
    request.path_info = new_path

    request.body = json.dumps({
        "actor": {
            "objectType": "person",
            "username": username
        }
    })


def check_deprecation(request, pattern, action):
    """
        Applies a deprecation fix
    """
    match = pattern(request.path_info)
    if match:
        action(request, match)
        return True

# Depreactions are sorted by matching frequency, so deprecations expected
# to occurr more frequently that others go first. to minimize the iterations.

DEPRECATIONS = [
    (people_subscriptions_resource_matcher, fix_deprecated_subscribe_user),
    (people_resource_matcher, fix_deprecated_create_user),
]
