# -*- coding: utf-8 -*-


def post_tunneling_factory(handler, registry):
    def post_tunneling_tween(request):
        overriden_method = request.headers.get('X-HTTP-Method-Override', None)
        is_valid_overriden_method = overriden_method in ['DELETE', 'PUT']
        is_POST_request = request.method.upper() == 'POST'
        if is_POST_request and is_valid_overriden_method:
            request.method = overriden_method
        response = handler(request)
        return response
    return post_tunneling_tween


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

        response = handler(request)

        if debug == '1' and user:
            response.content_type = 'text/html'
            response.text = u'<html><body>{}</body></html>'.format(response.text)
        return response

    return browser_debug_tween
