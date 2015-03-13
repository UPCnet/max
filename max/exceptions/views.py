# -*- coding: utf-8 -*-
"""
    Views to catch different exceptions across execution of a request
"""

from max.exceptions import DuplicatedItemError
from max.exceptions import Forbidden
from max.exceptions import InvalidPermission
from max.exceptions import InvalidSearchParams
from max.exceptions import MissingField
from max.exceptions import ObjectNotFound
from max.exceptions import ObjectNotSupported
from max.exceptions import Unauthorized
from max.exceptions import UnknownUserError
from max.exceptions import ValidationError
from max.exceptions.http import JSONHTTPBadRequest
from max.exceptions.http import JSONHTTPForbidden
from max.exceptions.http import JSONHTTPNotFound
from max.exceptions.http import JSONHTTPUnauthorized

from pyramid.view import view_config
from pyramid.view import forbidden_view_config
from pyramid.view import notfound_view_config

from bson.errors import InvalidId


@view_config(context=Unauthorized)
def unauthorized(exc, request):
    return JSONHTTPUnauthorized(error=dict(objectType='error', error=Unauthorized.__name__, error_description=exc.message))


@forbidden_view_config()
def main_forbidden(request):
    message = 'User "{}" has no permission "{}" here '.format(request.authenticated_userid, request.exception.result.permission)
    return JSONHTTPForbidden(error=dict(objectType='error', error=Forbidden.__name__, error_description=message))


@notfound_view_config()
def notfound(request):
    return JSONHTTPNotFound(error=dict(objectType='error', error=ObjectNotFound.__name__, error_description='Object {} not found'.format(request.exception.detail)))


@view_config(context=UnknownUserError)
def required_user(exc, request):
    return JSONHTTPBadRequest(error=dict(objectType='error', error=UnknownUserError.__name__, error_description=exc.message))


@view_config(context=InvalidId)
def invalid_id(exc, request):
    return JSONHTTPBadRequest(error=dict(objectType='error', error=InvalidId.__name__, error_description=exc.message))


@view_config(context=ObjectNotSupported)
def object_not_supported(exc, request):
    return JSONHTTPBadRequest(error=dict(objectType='error', error=ObjectNotSupported.__name__, error_description=exc.message))


@view_config(context=ObjectNotFound)
def object_not_found(exc, request):
    return JSONHTTPNotFound(error=dict(objectType='error', error=ObjectNotFound.__name__, error_description=exc.message))


@view_config(context=MissingField)
def missing_field(exc, request):
    return JSONHTTPBadRequest(error=dict(objectType='error', error=MissingField.__name__, error_description=exc.message))


@view_config(context=DuplicatedItemError)
def duplicated_item_error(exc, request):
    return JSONHTTPBadRequest(error=dict(objectType='error', error=DuplicatedItemError.__name__, error_description=exc.message))


@view_config(context=InvalidSearchParams)
def invalid_search_params(exc, request):
    return JSONHTTPBadRequest(error=dict(objectType='error', error=InvalidSearchParams.__name__, error_description=exc.message))


@view_config(context=InvalidPermission)
def invalid_permission(exc, request):
    return JSONHTTPBadRequest(error=dict(objectType='error', error=InvalidPermission.__name__, error_description=exc.message))


@view_config(context=ValidationError)
def validation_error(exc, request):
    return JSONHTTPBadRequest(error=dict(objectType='error', error=ValidationError.__name__, error_description=exc.message))


@view_config(context=Forbidden)
def forbidden(exc, request):
    return JSONHTTPForbidden(error=dict(objectType='error', error=Forbidden.__name__, error_description=exc.message))
