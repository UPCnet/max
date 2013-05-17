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

