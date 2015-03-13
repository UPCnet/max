# -*- coding: utf-8 -*-
"""JSON HTTP Exceptions

These are regular HTTPExceptions, each with its related code
all expecting a dict object to convert to JSON, and set
the correct content_type"""

from pyramid.httpexceptions import HTTPException

import json


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
