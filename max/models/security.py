# -*- coding: utf-8 -*-
from max.MADObjects import MADBase
from max.security import Manager
from max.security.permissions import manage_security

from pyramid.decorator import reify
from pyramid.security import Allow


class Security(MADBase):
    """
        The Security object representation
    """
    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, manage_security)
        ]
        return acl

    default_field_view_permission = manage_security
    default_field_edit_permission = manage_security
    collection = 'security'
    unique = '_id'
    schema = {
        '_id': {},
        'roles': {}
    }
