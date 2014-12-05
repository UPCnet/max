# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPException

import json

# Base exception classes


class JSONHTTPException(HTTPException):
    """
        Base exception class for all exceptions raised as the result
        of an error, to provide a message to the client
    """
    def __init__(self, error):
        """
            Configures exception and inner response status code, content
            and content_type
        """
        super(JSONHTTPException, self).__init__(body=json.dumps(error))
        self.content_type = 'application/json'


# JSON HTTP Exceptions

# These are regular HTTPExceptions, each with its related code
# all expecting a dict object to convert to JSON, and set
# the correct content_type


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


# Max Exceptions

# These are meant to be raised through model and endpoints code, and all
# of them matches one of the prior defined JSON HTTP Exceptions


class MissingField(Exception):
    pass


class ObjectNotSupported(Exception):
    pass


class ObjectNotFound(Exception):
    pass


class DuplicatedItemError(Exception):
    pass


class UnknownUserError(Exception):
    pass


class Unauthorized(Exception):
    pass


class InvalidSearchParams(Exception):
    pass


class InvalidPermission(Exception):
    pass


class ValidationError(Exception):
    pass


class Forbidden(Exception):
    pass


class ConnectionError(Exception):
    pass
