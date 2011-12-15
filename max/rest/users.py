from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk, HTTPNotFound, HTTPInternalServerError

import json
from pymongo.objectid import ObjectId

from max.resources import Root
from max.rest.utils import checkDataAddUser, checkRequestConsistency, extractPostData

from max.MADMax import MADMaxDB,MADMaxCollection
from max.models import User
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity

import datetime
       

@view_config(route_name='users', request_method='GET')
class UsersGetter(JSONResourceRoot):
    """
    """
    def __call__(self):
        """
        """
        mmdb = MADMaxDB(self.context.db)
        users = mmdb.users.dump()
        return self.buildResponse(users)

@view_config(route_name='user', request_method='GET')
class UserGetter(JSONResourceEntity):
    """
    """
    def __call__(self):
        """
        """
        displayName = self.request.matchdict['user_displayName']

        users = MADMaxCollection(self.context.db.users,query_key='displayName')
        user = users[displayName]

        return self.buildResponse(user)

@view_config(route_name='user', request_method='POST')
class UserAdder(JSONResourceEntity):
    """
    """
    def __call__(self):
        """
        """
        displayName = self.request.matchdict['user_displayName']

        newuser = User(request)
        userid = newuser.insert()

        return self.buildResponse(userid)
