# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPFound

from pyramid.url import resource_url
from pyramid.interfaces import IAuthenticationPolicy

from pyramid.security import forget

from urlparse import urljoin

import datetime

from max.views.api import TemplateAPI
import requests
import json


def _fixup_came_from(request, came_from):
    if came_from is None:
        return request.application_url
    came_from = urljoin(request.application_url, came_from)
    if came_from.endswith('login'):
        came_from = came_from[:-len('login')]
    elif came_from.endswith('logout'):
        came_from = came_from[:-len('logout')]
    return came_from


def login(context, request):
    page_title = "MAX Server Login"
    api = TemplateAPI(context, request, page_title)

    # came_from on the fridge
    # came_from = _fixup_came_from(request, request.POST.get('came_from'))

    login_url = resource_url(request.context, request, 'login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use the login form itself as came_from

    reason = ''
    login = ''
    password = ''

    if request.params.get('form.submitted', None) is not None:

        policy = request.registry.queryUtility(IAuthenticationPolicy)
        authapi = policy._getAPI(request)

        #challenge_qs = {'came_from': came_from}
        # identify
        login = request.POST.get('login')
        password = request.POST.get('password')
        if login is None or password is None:
            return HTTPFound(location='%s/login' % api.application_url)

        credentials = {'login': login, 'password': password}

        userid, headers = authapi.login(credentials)

        # if not successful, try again
        if not userid:
            #challenge_qs['reason'] = reason

            return dict(
                    message=reason,
                    url=api.application_url + '/login',
#                    came_from=came_from,
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

        return HTTPFound(headers=headers, location=api.application_url)

    response = dict(
            message=reason,
            url=api.application_url + '/login',
            # came_from=came_from,
            login=login,
            password=password,
            api=api
            )

    return response


def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.resource_url(request.context), headers=headers)
