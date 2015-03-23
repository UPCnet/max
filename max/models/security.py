# -*- coding: utf-8 -*-
from max.MADObjects import MADBase


class Security(MADBase):
    """
        The Security object representation
    """
    def __acl__(self):
        acl = []
        return acl

    collection = 'security'
    unique = '_id'
    schema = {
        '_id': {},
        'roles': {}
    }
