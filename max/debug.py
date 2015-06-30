from pyramid.settings import asbool
from urllib import unquote_plus


def patched_check_token(*args, **kwargs):
    return True


def browser_debug_factory(handler, registry):
    def browser_debug_tween(request):
        debug = request.params.get('d', None)
        debugging = debug is not None
        if debugging:
            user = request.params.get('u', None)
            token = request.params.get('t', 'fake_token')
            method = request.params.get('m', '').upper()
            payload = request.params.get('p', None)

            if user:
                new_headers = {
                    'X-Oauth-Token': token,
                    'X-Oauth-Username': user,
                    'X-Oauth-Scope': 'widgetcli'
                }
                request.headers.update(new_headers)

                if method in ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']:
                    request.method = method.upper()

                if payload:
                    request.text = payload

        request.body = unquote_plus(request.body).strip('=')
        request.headers['Content-Type'] = 'application/json'
        response = handler(request)

        if debug == '1' and user:
            response.content_type = 'text/html'
            response.text = u'<html><body>{}</body></html>'.format(response.text)
        return response

    return browser_debug_tween


def setup(settings):
    if asbool(settings['max.debug_api']):
        if asbool(settings.get('testing', False)):  # pragma: no cover
            settings['pyramid.tweens'].insert(1, 'max.debug.browser_debug_factory')
        else:  # pragma: no cover
            settings['pyramid.tweens'].append('max.debug.browser_debug_factory')

    if asbool(settings['max.oauth_passtrough']):
        import max.security.authentication
        max.security.authentication.check_token = patched_check_token
