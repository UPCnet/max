# -*- coding: utf-8 -*-
"""Max Exceptions

These are meant to be raised through model and endpoints code, and all
of them matches one of the prior defined JSON HTTP Exceptions"""


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
