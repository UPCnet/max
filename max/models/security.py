# -*- coding: utf-8 -*-
from max.MADObjects import MADBase


class Security(MADBase):
    """
        The Security object representation
    """
    collection = 'security'
    unique = '_id'
    schema = {'_id':         dict(required=0),
              'roles':        dict(required=0)}
