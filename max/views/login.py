# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPFound

from pyramid.url import resource_url
from pyramid.interfaces import IAuthenticationPolicy

from pyramid.security import forget

from urlparse import urljoin

import datetime

from max.views.api import TemplateAPI


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

    page_title = "MAX Login"
    api = TemplateAPI(context, request, page_title)

    came_from = _fixup_came_from(request, request.POST.get('came_from'))

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

        challenge_qs = {'came_from': came_from}
        # identify
        login = request.POST.get('login')
        password = request.POST.get('password')
        if login is None or password is None:
            return HTTPFound(location='%s/login?'
                                        % request.application_url)
        credentials = {'login': login, 'password': password}

        userid, headers = authapi.login(credentials)

        # if not successful, try again
        if not userid:
            challenge_qs['reason'] = reason
            # return HTTPFound(location='%s/login?%s'
            #                  % (request.application_url,
            #                     urlencode(challenge_qs, doseq=True)))
            return dict(
                    message=reason,
                    url=request.application_url + '/login',
                    came_from=came_from,
                    login=login,
                    password=password,
                    api=api
                    )

        # If it's the first time the user log in the system, then create the local user structure
        user = context.db.users.find_one({'displayName': userid['repoze.who.userid']})

        if user:
            # User exist in database, update login time and continue
            user['last_login'] = datetime.datetime.now()
            context.db.users.save(user)
        else:
            # No userid found in the database, then create an instance
            newuser = {'displayName': userid['repoze.who.userid'],
                       'last_login': datetime.datetime.now(),
                       'following': {'items': [], },
                       'subscribedTo': {'items': [], }
                       }
            context.db.users.save(newuser)

        return HTTPFound(headers=headers, location=came_from)

    response = dict(
            message=reason,
            url=request.application_url + '/login',
            came_from=came_from,
            login=login,
            password=password,
            api=api
            )

    return response


def logout(request):
    headers = forget(request)
    return HTTPFound(location=request.resource_url(request.context),
                     headers=headers)
