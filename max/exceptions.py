# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPException
from pyramid.response import Response

import json

"""

    Base exception classes

"""


class JSONHTTPException(HTTPException):
    def __init__(self, error):
        Response.__init__(self, json.dumps(error), status=self.code)
        self.content_type = 'application/json'


class MaxException(Exception):
    def __init__(self, value):
        self.value = value


"""
    JSON HTTP Exceptions

    These are regular HTTPExceptions, each with its related code
    all expecting a dict object to convert to JSON, and set
    the correct content_type
"""


class JSONHTTPUnauthorized(JSONHTTPException):
    code = 401


class JSONHTTPForbidden(JSONHTTPException):
    code = 403


class JSONHTTPBadRequest(JSONHTTPException):
    code = 400


class JSONHTTPNotFound(JSONHTTPException):
    code = 404


class JSONHTTPNotImplemented(JSONHTTPException):
    code = 501


class JSONHTTPInternalServerError(JSONHTTPException):  # pragma: no cover
    code = 500


class JSONHTTPServiceUnavailable(JSONHTTPException):  # pragma: no cover
    code = 503


class JSONHTTPPreconditionFailed(JSONHTTPException):  # pragma: no cover
    code = 412


"""

    Max Exceptions

    These are meant to be raised through model and endpoints code, and all
    of them matches one of the prior defined JSON HTTP Exceptions

"""


class MissingField(MaxException):
    pass


class ObjectNotSupported(MaxException):
    pass


class ObjectNotFound(MaxException):
    pass


class DuplicatedItemError(MaxException):
    pass


class UnknownUserError(MaxException):
    pass


class Unauthorized(MaxException):
    pass


class InvalidSearchParams(MaxException):
    pass


class InvalidPermission(MaxException):
    pass


class ValidationError(MaxException):
    pass


class Forbidden(MaxException):
    pass


class ConnectionError(MaxException):
    pass
