# -*- coding: utf-8 -*-

from zope.interface import implementer

from max.exceptions import Unauthorized
from max.resources import getMAXSettings
from max.security import Owner

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Authenticated
from pyramid.security import Everyone
from pyramid.settings import asbool

from beaker.cache import cache_region

import requests


@cache_region('oauth_token')
def check_token(url, username, token, scope, oauth_standard):
    """
        Checks if a user matches the given token.
    """
    if oauth_standard:
        payload = {"access_token": token, "username": username}
        payload['scope'] = scope if scope else 'widgetcli'
    else:
        payload = {"oauth_token": token, "user_id": username}
        payload['scope'] = scope if scope else 'widgetcli'
    return requests.post(url, data=payload, verify=False).status_code == 200


@implementer(IAuthenticationPolicy)
class MaxAuthenticationPolicy(object):
    """
        Pyramid authentication policy against OAuth2 provided on headers
        and principals stored on database.
    """
    def __init__(self, allowed_scopes):
        self.allowed_scopes = allowed_scopes
        self._authenticated_userid = ''

    def _validate_user(self, request):
        """
            Extracts and validates user from the request.

            Performs several checks that will result on Unauthorized
            exceptions if failed. At the end the successfully authenticated
            username is returned.

            Method is reified to assure that is only called once per request.
        """
        settings = getMAXSettings(request)

        oauth_token = request.headers.get('X-Oauth-Token', '')
        username = request.headers.get('X-Oauth-Username', '')
        scope = request.headers.get('X-Oauth-Scope', '')

        if not oauth_token or not username:
            # This is for mental sanity in case we miss the body part when writing tests
            if 'X-Oauth-Username' in request.params.keys():
                raise Unauthorized("Authorization found in url params, not in request. Check your tests, you may be passing the authentication headers as the request body...")

            raise Unauthorized('No auth headers found.')

        if scope not in self.allowed_scopes:
            raise Unauthorized('The specified scope is not allowed for this resource.')

        valid = check_token(
            settings['max_oauth_check_endpoint'],
            username, oauth_token, scope,
            asbool(settings.get('max_oauth_standard', False)))

        if not valid:
            raise Unauthorized('Invalid token.')

        return username

    def authenticated_userid(self, request):
        """
            Returns the oauth2 authenticated user. If anything fails during
            validation raises an exception
        """
        return self._authenticated_userid if self._authenticated_userid else self._validate_user(request)

    def unauthenticated_userid(self, request):
        """
            DUP of authenticated_userid
        """
        return self.authenticated_userid

    def effective_principals(self, request):
        """
            Returns the effective identities that can be used
            when authorizing the user
        """

        # The
        principals = self.authenticated_userid
        principals = [Everyone, Authenticated]
        if request.context._owner == request.authenticated_userid:
            principals.append(Owner)
        return principals

    def remember(self, request, principal, **kw):
        """ Not used neither needed """
        return []

    def forget(self, request):
        """ Not used neither needed"""
        return []
