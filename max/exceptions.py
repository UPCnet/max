from pyramid.httpexceptions import HTTPUnauthorized, HTTPBadRequest, HTTPNotImplemented
from pyramid.response import Response

import json


class JSONHTTPUnauthorized(HTTPUnauthorized):

    def __init__(self, error):
        Response.__init__(self, json.dumps(error), status=self.code)
        self.content_type = 'application/json'


class JSONHTTPBadRequest(HTTPBadRequest):

    def __init__(self, error):
        Response.__init__(self, json.dumps(error), status=self.code)
        self.content_type = 'application/json'


class JSONHTTPNotImplemented(HTTPNotImplemented):

    def __init__(self, error):
        Response.__init__(self, json.dumps(error), status=self.code)
        self.content_type = 'application/json'


class MissingField(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ObjectNotSupported(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ObjectNotFound(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class DuplicatedItemError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class UnknownUserError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Unauthorized(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class InvalidSearchParams(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class InvalidPermission(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
