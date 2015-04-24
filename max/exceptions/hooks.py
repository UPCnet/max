# -*- coding: utf-8 -*-
from pyramid.view import forbidden_view_config
from max.exceptions import Forbidden
from max.exceptions.http import JSONHTTPForbidden


@forbidden_view_config()
def main_forbidden(request):
    """
        This view pops up when an authorization error occurs in the pyramid pipeline.

        NOTE: There is another forbidden view just below here, that catches the
        Forbidden exceptions inside endpoint code.
    """
    message = 'User "{}" has no permission "{}" here '.format(request.authenticated_userid, request.exception.result.permission)
    return JSONHTTPForbidden(error=dict(objectType='error', error=Forbidden.__name__, error_description=message))
