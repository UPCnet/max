# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPFound

from pyramid.view import view_config
from pyramid.url import resource_url
from pyramid.view import forbidden_view_config
from pyramid.interfaces import IAuthenticationPolicy

from pyramid.security import forget

import datetime

from max.rest.resources import RESOURCES
from max.exceptions import JSONHTTPUnauthorized
from max.views.api import TemplateAPI
import requests
import json


@view_config(name='login', renderer='max:templates/login.pt')
@forbidden_view_config(renderer='max:templates/login.pt')
def login(context, request):
    """ The login view - pyramid_who enabled with the forbidden view logic.
    """

    page_title = "MAX Server Login"
    api = TemplateAPI(context, request, page_title)

    # Catch unauthorized requests and answer with an JSON error if it is a REST service.
    # Otherwise, show the login form.
    if getattr(request.matched_route, 'name', None) in RESOURCES:
        return JSONHTTPUnauthorized(error=dict(error='RestrictedService', error_description="You don't have permission to access this service"))

    login_url = resource_url(request.context, request, 'login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use the login form itself as came_from

    came_from = request.params.get('came_from', referrer)
    message = ''
    login = ''
    password = ''

    if request.params.get('form.submitted', None) is not None:

        policy = request.registry.queryUtility(IAuthenticationPolicy)
        authapi = policy._getAPI(request)

        # identify
        login = request.POST.get('login')
        password = request.POST.get('password')

        if login is u'' or password is u'':
            return dict(
                    message='You need to suply an username and a password.',
                    url=api.application_url + '/login',
                    came_from=came_from,
                    login=login,
                    password=password,
                    api=api
                    )

        credentials = {'login': login, 'password': password}

        userid, headers = authapi.login(credentials)

        # if not successful, try again
        if not userid:
            return dict(
                    message='Login failed. Please try again.',
                    url=api.application_url + '/login',
                    came_from=came_from,
                    login=login,
                    password=password,
                    api=api
                    )

        # If it's the first time the user log in the system, then create the local user structure
        user = context.db.users.find_one({'username': userid['repoze.who.userid']})

        if user:
            # User exist in database, update login time and continue
            user['last_login'] = datetime.datetime.now()
            context.db.users.save(user)
        else:
            # No userid found in the database, then create an instance
            newuser = {'username': userid['repoze.who.userid'],
                       'last_login': datetime.datetime.now(),
                       'following': {'items': [], },
                       'subscribedTo': {'items': [], }
                       }
            context.db.users.save(newuser)

        OAUTH_SERVER = 'https://oauth.upc.edu'
        GRANT_TYPE = 'password'
        CLIENT_ID = 'MAX'
        SCOPE = 'widgetcli'

        username = login

        REQUEST_TOKEN_ENDPOINT = '%s/token' % (OAUTH_SERVER)

        payload = {"grant_type": GRANT_TYPE,
                   "client_id": CLIENT_ID,
                   "scope": SCOPE,
                   "username": username,
                   "password": password
                   }

        req = requests.post(REQUEST_TOKEN_ENDPOINT, data=payload, verify=False)
        response = json.loads(req.text)
        oauth_token = response.get("oauth_token")

        request.session['oauth_token'] = oauth_token

        # Finally, return the authenticated view
        return HTTPFound(headers=headers, location=came_from)

    return dict(
            message=message,
            url=api.application_url + '/login',
            came_from=came_from,
            login=login,
            password=password,
            api=api
            )


@view_config(name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.resource_url(request.context), headers=headers)
