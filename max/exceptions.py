# -*- coding: utf-8 -*-
from pyramid.httpexceptions import HTTPUnauthorized, HTTPBadRequest, HTTPNotImplemented, HTTPNotFound, HTTPForbidden, HTTPInternalServerError
from pyramid.response import Response

import json


class JSONHTTPUnauthorized(HTTPUnauthorized):

    def __init__(self, error):
        Response.__init__(self, json.dumps(error), status=self.code)
        self.content_type = 'application/json'


class JSONHTTPForbidden(HTTPForbidden):

    def __init__(self, error):
        Response.__init__(self, json.dumps(error), status=self.code)
        self.content_type = 'application/json'


class JSONHTTPBadRequest(HTTPBadRequest):

    def __init__(self, error):
        Response.__init__(self, json.dumps(error), status=self.code)
        self.content_type = 'application/json'


class JSONHTTPNotFound(HTTPNotFound):

    def __init__(self, error):
        Response.__init__(self, json.dumps(error), status=self.code)
        self.content_type = 'application/json'


class JSONHTTPNotImplemented(HTTPNotImplemented):

    def __init__(self, error):
        Response.__init__(self, json.dumps(error), status=self.code)
        self.content_type = 'application/json'


class JSONHTTPInternalServerError(HTTPInternalServerError):  # pragma: no cover

    def __init__(self, error):
        Response.__init__(self, json.dumps(error), status=self.code)
        self.content_type = 'application/json'


class MissingField(Exception):
    def __init__(self, value):
        self.value = value


class ObjectNotSupported(Exception):
    def __init__(self, value):
        self.value = value


class ObjectNotFound(Exception):
    def __init__(self, value):
        self.value = value


class DuplicatedItemError(Exception):
    def __init__(self, value):
        self.value = value


class UnknownUserError(Exception):
    def __init__(self, value):
        self.value = value


class Unauthorized(Exception):
    def __init__(self, value):
        self.value = value


class InvalidSearchParams(Exception):
    def __init__(self, value):
        self.value = value


class InvalidPermission(Exception):
    def __init__(self, value):
        self.value = value


class ValidationError(Exception):
    def __init__(self, value):
        self.value = value


class Forbidden(Exception):
    def __init__(self, value):
        self.value = value