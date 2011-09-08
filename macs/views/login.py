from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized

from pyramid.url import resource_url

from pyramid.security import remember
from pyramid.security import forget

from urlparse import urljoin

import datetime


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

#    import ipdb; ipdb.set_trace()

    plugins = request.environ.get('repoze.who.plugins', {})
    auth_tkt = plugins.get('auth_tkt')

    came_from = _fixup_came_from(request, request.POST.get('came_from'))

    login_url = resource_url(request.context, request, 'login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use the login form itself as came_from

    reason = ''
    login = ''
    password = ''

    if request.params.get('form.submitted', None) is not None:

        challenge_qs = {'came_from': came_from}
        # identify
        login = request.POST.get('login')
        password = request.POST.get('password')
        if login is None or password is None:
            return HTTPFound(location='%s/login?'
                                        % request.application_url)
        credentials = {'login': login, 'password': password}

        # authenticate
        authenticators = filter(None, [plugins.get(name) for name in ['htpasswd']])

        userid = None
        # import ipdb; ipdb.set_trace()
        if authenticators:
            reason = 'Bad username or password'
        else:
            reason = 'No authenticatable users'

        for plugin in authenticators:
            userid = plugin.authenticate(request.environ, credentials)
            if userid:
                break

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
                  )
        # else, remember
        credentials['repoze.who.userid'] = userid
        if auth_tkt is not None:
            remember_headers = auth_tkt.remember(request.environ, credentials)
        else:
            remember_headers = []

        # If it's the first time the user log in the system, then create the local user structure

        user = context.db.users.find_one({'username': userid})

        if user:
            # User exist in database, update login time and continue
            user['last_login'] = datetime.datetime.now()
            context.db.users.save(user)
        else:
            # No userid found in the database, then create an instance
            newuser = {'username': userid, 'last_login': datetime.datetime.now()}
            context.db.users.save(newuser)

            # In case it's needed to redirect the new user to his/her profilepage
            # return HTTPFound(headers=remember_headers, location='%s/editProfile' % request.application_url)

        return HTTPFound(headers=remember_headers, location=came_from)

    response = dict(
            message=reason,
            url=request.application_url + '/login',
            came_from=came_from,
            login=login,
            password=password,
            )

    return response


def logout(request, reason='Logged out'):
    unauthorized = HTTPUnauthorized()
    unauthorized.headerlist.append(
        ('X-Authorization-Failure-Reason', reason))
    return unauthorized
