from max.exceptions import Unauthorized
from max.resources import getMAXSettings
from max.resources import Root

import requests


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

            if allowed_scopes:
                if scope not in allowed_scopes:
                    raise Unauthorized('The specified scope is not allowed for this resource.')

            # Validate access token
            payload = {"oauth_token": oauth_token,
                       "user_id": username,
                       }
            if scope:
                payload['scope'] = scope

            req = requests.post(settings['max_oauth_check_endpoint'], data=payload, verify=False)

            # FOR DEBUGGING, oauth passtrough
            # if req:
            if req.status_code == 200:
                Valid token, proceed.

                def getCreator(request):
                    return username

                request.set_property(getCreator, name='creator', reify=True)

                return view_function(*args, **kw)
            else:
                raise Unauthorized('Invalid token.')

        new_function.__doc__ = view_function.__doc__
        return new_function
    if type(allowed_scopes) == type(wrap):
        return wrap(allowed_scopes)
    return wrap
