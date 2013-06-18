from max.exceptions import Unauthorized
from max.resources import getMAXSettings
from max.resources import Root

from pyramid.settings import asbool

import requests
from beaker.cache import cache_region


@cache_region('oauth_token')
def checkToken(url, username, token, scope, oauth_standard):
    if oauth_standard:
        payload = {"access_token": token, "username": username}
        payload['scope'] = scope if scope else 'widgetcli'
    else:
        payload = {"oauth_token": token, "user_id": username}
        payload['scope'] = scope if scope else 'widgetcli'
    return requests.post(url, data=payload, verify=False).status_code == 200


def oauth2(allowed_scopes=[]):
    def wrap(view_function):
        def new_function(*args, **kw):
            nkargs = [a for a in args]
            context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])

            # Extract the username and token from request headers
            # It will be like:
            # headers = {"X-Oauth-Token": "jfa1sDF2SDF234", "X-Oauth-Username": "messi", "X-Oauth-Scope": "widgetcli"}
            settings = getMAXSettings(request)

            oauth_token = request.headers.get('X-Oauth-Token', '')
            username = request.headers.get('X-Oauth-Username', '')
            scope = request.headers.get('X-Oauth-Scope', '')

            if not oauth_token or not username:

                # This is for mental sanity in case we miss the body part when writing tests
                if 'X-Oauth-Username' in request.params.keys():
                    raise Unauthorized("Authorization found in url params, not in request. Check your tests, you may be passing the authentication headers as the request body...")

                raise Unauthorized('No auth headers found.')

            if scope not in allowed_scopes:
                raise Unauthorized('The specified scope is not allowed for this resource.')

            valid = checkToken(settings['max_oauth_check_endpoint'], username, oauth_token, scope, asbool(settings.get('max_oauth_standard', False)))

            if valid:
                def getCreator(request):
                    return username

                request.set_property(getCreator, name='creator', reify=True)

                return view_function(*args, **kw)
            else:
                raise Unauthorized('Invalid token.')

        new_function.__doc__ = view_function.__doc__
        return new_function
    return wrap
