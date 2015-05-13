# -*- coding: utf-8 -*-
import re
from hashlib import sha1

people_resource_matcher = re.compile(r'/people/([^\/]+)$').search
people_subscriptions_resource_matcher = re.compile(r'/people/([^\/]+)/subscriptions$').search
people_subscription_resource_matcher = re.compile(r'/people/([^\/]+)/subscriptions/([^\/]+)$').search
people_activities_resource_matcher = re.compile(r'/people/([^\/]+)/activities$').search
people_conversation_resource_matcher = re.compile(r'/people/([^\/]+)/conversations/([^\/]+)$').search
people_device_token_resource_matcher = re.compile(r'/people/([^\/]+)/device/([^\/]+)/([^\/]+)$').search


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
    payload = request.decoded_payload
    payload = payload if isinstance(payload, dict) else {}
    payload['username'] = username
    request.path_info = '/people'

    # Force headers needed to avoid body content quoting on tests
    request.headers['Content-Type'] = 'application/json'


def fix_deprecated_subscribe_user(request, match):
    """
        Adapts the deprecated way to subscribe an user to a context

        Requests matching:

            POST /people/{user}/subscriptions

        will be transformed into:

            POST /contexts/{hash}/subscriptions

        Hash will be extracted from the url on the json body,
        and a actor parameter will be injected into the json body,
        using username found in the url.

        In the case that body doesn't contain a context to post to
        it will be interpretated as a regular user timeline post, and remain
        untouched
    """
    username = match.groups()[0]
    payload = request.decoded_payload
    payload = payload if isinstance(payload, dict) else {}
    obj = payload.pop('object', {})
    object_url = obj.get('url', None)
    url_hash = sha1(object_url).hexdigest() if object_url else ''
    new_path = '/contexts/{}/subscriptions'.format(url_hash)
    request.path_info = new_path

    payload.update({
        "actor": {
            "objectType": "person",
            "username": username
        }
    })

    # Force headers needed to avoid body content quoting on tests
    request.headers['Content-Type'] = 'application/json'


def fix_deprecated_unsubscribe_user(request, match):
    """
        Adapts the deprecated way to unsubscribe an user to a context

        Requests matching:

            DELETE /people/{username}/subscriptions/{hash}

        will be transformed into:

            DELETE /contexts/{hash}/subscriptions/{username}

        There are no substancial changes, only a simple rewrite of the url.
    """
    username = match.groups()[0]
    chash = match.groups()[1]

    new_path = '/contexts/{}/subscriptions/{}'.format(chash, username)
    request.path_info = new_path

    # Force headers needed to avoid body content quoting on tests
    request.headers['Content-Type'] = 'application/json'


def fix_deprecated_create_context_activity(request, match):
    """

        Adapts the deprecated way to post an activity to a context,
        when the actor is a Person

        Requests matching:

            POST /people/{username}/activities

        will be transformed into:

            POST /contexts/{hash}/activities

        Hash will be extracted from the url on the json body,
        and a actor parameter will be injected into the json body,
        using username found in the url
    """
    username = match.groups()[0]
    payload = request.decoded_payload
    payload = payload if isinstance(payload, dict) else {}
    contexts = payload.pop('contexts', {})
    if contexts:
        context = contexts[0]
        context_url = context.get('url', None)
        url_hash = sha1(context_url).hexdigest() if context_url else ''
        new_path = '/contexts/{}/activities'.format(url_hash)
        request.path_info = new_path

        payload.update({
            "actor": {
                "objectType": "person",
                "username": username
            }
        })

        # Force headers needed to avoid body content quoting on tests
        request.headers['Content-Type'] = 'application/json'


def fix_deprecated_join_conversation(request, match):
    """
        Adapts the deprecated way to subscribe an user to a conversation

        Requests matching:

            POST /people/{user}/conversations/{id}

        will be transformed into:

            POST /conversations/{id}/participants

        id will be extracted from the url on the json body,
        and a actor parameter will be injected into the json body,
        using username found in the url.

        Original request body will be ignored, as the original request format
        didn't expect any input from it.

    """
    username = match.groups()[0]
    conversation_id = match.groups()[1]
    payload = request.decoded_payload
    payload = payload if isinstance(payload, dict) else {}
    payload.clear()

    new_path = '/conversations/{}/participants'.format(conversation_id)
    request.path_info = new_path

    payload.update({
        "actor": {
            "objectType": "person",
            "username": username
        }
    })

    # Force headers needed to avoid body content quoting on tests
    request.headers['Content-Type'] = 'application/json'


def fix_deprecated_leave_conversation(request, match):
    """
        Adapts the deprecated way to subscribe an user to a conversation

        Requests matching:

            DELETE /people/{username}/conversations/{id}

        will be transformed into:

            DELETE /conversations/{id}/participants/{username}

        id will be extracted from the url on the json body,
        and a actor parameter will be injected into the json body,
        using username found in the url.

        Original request body will be ignored, as the original request format
        didn't expect any input from it.

    """
    username = match.groups()[0]
    conversation_id = match.groups()[1]

    new_path = '/conversations/{}/participants/{}'.format(conversation_id, username)
    request.path_info = new_path

    # Force headers needed to avoid body content quoting on tests
    request.headers['Content-Type'] = 'application/json'


def fix_deprecated_add_token(request, match):
    """
        Adapts the deprecated way to add a token

        Requests matching:

            POST /people/{username}/device/{platform}/{token}

        will be transformed into:

            POST /tokens

        platform and token will be extracted from the url on the json body,
        and a conveninent request body will be generated using those params.

        Original request body will be ignored, as the original request format
        didn't expect any input from it. The original request format neither accepted
        impersonation, so we'll ignore username in the url, and use the authenticated one.

    """
    platform = match.groups()[1]
    token = match.groups()[2]

    payload = request.decoded_payload
    payload = payload if isinstance(payload, dict) else {}
    payload.clear()

    payload.update({
        'platform': platform,
        'token': token
    })
    new_path = '/tokens'
    request.path_info = new_path

    # Force headers needed to avoid body content quoting on tests
    request.headers['Content-Type'] = 'application/json'

    def wrapper(response):
        """
            Replaces response body with the request actor,
            as expected by the older api
        """
        import json
        response.body = json.dumps(request.actor.getInfo())
        return response

    return wrapper


def fix_deprecated_delete_token(request, match):
    """
        Adapts the deprecated way to add a token

        Requests matching:

            DELETE /people/{username}/device/{platform}/{token}

        will be transformed into:

            DELETE /tokens/{id}

        token will be extracted from the url on the json body,
        and remapped to its new url location.

        Original request body will be ignored, as the original request format
        didn't expect any input from it. The original request format neither accepted
        impersonation, so we'll ignore username in the url, and use the authenticated one.
        Platform is also ignored, as we'll identify the token by itself.

    """
    token = match.groups()[2]
    new_path = '/tokens/{}'.format(token)
    request.path_info = new_path

    # Force headers needed to avoid body content quoting on tests
    request.headers['Content-Type'] = 'application/json'


def check_deprecation(request, pattern, action):
    """
        Applies a deprecation fix
    """
    match = pattern(request.path_info)
    if match:
        response_wrapper = action(request, match)
        return True, response_wrapper

    return False, None

# PLEASE! Construct depreaction list sorted by matching frequency, so deprecations expected
# to happen more frequently that others go first. This is to minimize the number of deprecations tested

POST_DEPRECATIONS = [
    (people_activities_resource_matcher, fix_deprecated_create_context_activity),
    (people_subscriptions_resource_matcher, fix_deprecated_subscribe_user),
    (people_resource_matcher, fix_deprecated_create_user),
    (people_conversation_resource_matcher, fix_deprecated_join_conversation),
    (people_device_token_resource_matcher, fix_deprecated_add_token)
]

DELETE_DEPRECATIONS = [
    (people_subscription_resource_matcher, fix_deprecated_unsubscribe_user),
    (people_conversation_resource_matcher, fix_deprecated_leave_conversation),
    (people_device_token_resource_matcher, fix_deprecated_delete_token)
]
