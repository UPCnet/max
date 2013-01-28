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

            r = requests.post(settings['max_oauth_check_endpoint'], data=payload, verify=False)

            if r.status_code == 200:
                # Valid token, proceed.
                return view_function(*args, **kw)
            else:
                return view_function(*args, **kw)
                # raise Unauthorized('Invalid token.')

        new_function.__doc__ = view_function.__doc__
        return new_function
    if type(allowed_scopes) == type(wrap):
        return wrap(allowed_scopes)
    return wrap


def oauth2_restricted(allowed_roles=[]):
    def wrap(view_function):
        def new_function(*args, **kw):
            nkargs = [a for a in args]
            context, request = isinstance(nkargs[0], Root) and tuple(nkargs) or tuple(nkargs[::-1])

            # Extract the username and token from request headers
            username = request.headers.get('X-Oauth-Username', '')

            security = request.registry.max_security
            for role in allowed_roles:
                if username in security.get(role):
                    # Valid allowed user token, proceed.
                    return view_function(*args, **kw)
                else:
                    raise Unauthorized('The provided credentials are not allowed to perform this operation.')

        new_function.__doc__ = view_function.__doc__
        return new_function
    if type(allowed_roles) == type(wrap):
        return wrap(allowed_roles)
    return wrap
