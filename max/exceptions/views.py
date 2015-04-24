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
from max.exceptions.http import JSONHTTPInternalServerError
from max.exceptions.http import JSONHTTPNotFound
from max.exceptions.http import JSONHTTPUnauthorized
from max.exceptions.scavenger import saveException

from pyramid.settings import asbool
from pyramid.view import view_config

from bson.errors import InvalidId

import traceback


@view_config(context=Unauthorized)
def unauthorized(exc, request):
    return JSONHTTPUnauthorized(error=dict(objectType='error', error=Unauthorized.__name__, error_description=exc.message))


@view_config(context=Forbidden)
def forbidden(exc, request):
    return JSONHTTPForbidden(error=dict(objectType='error', error=Forbidden.__name__, error_description=exc.message))


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


@view_config(context=Exception)
def scavenger(exc, request):
    error = traceback.format_exc()
    sha1_hash, log = saveException(request, error)
    max_server = request.environ.get('HTTP_X_VIRTUAL_HOST_URI', '')

    error_description = 'Your error has been logged at {}/exceptions/{}. Please contact the system admin.'.format(max_server, sha1_hash)
    if asbool(request.registry.settings.get('testing', False)) or asbool(request.registry.settings.get('max.include_traceback_in_500_errors', False)):  # pragma: no cover
        error_description = 'An exception occurred. Below is the catched exception.\n\nSorry for the convenience.\n\n' + log.replace('\n', '\n    ')[:-4]
    return JSONHTTPInternalServerError(error=dict(objectType='error', error='ServerError', error_description=error_description))
