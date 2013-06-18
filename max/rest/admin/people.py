# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent

from max.models import User
from max.oauth2 import oauth2
from max.decorators import MaxResponse, requirePersonActor
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.rest.utils import searchParams
from max.exceptions import ObjectNotFound


@view_config(route_name='users', request_method='GET', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def getUsers(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    users = mmdb.users.search({}, flatten=1, **searchParams(request))
    handler = JSONResourceRoot(users)
    return handler.buildResponse()


@view_config(route_name='user', request_method='DELETE', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def deleteUser(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    username = request.matchdict.get('username')
    found_user = mmdb.users.getItemsByusername(username)
    if not found_user:
        raise ObjectNotFound("There's no user with username: %s" % username)

    found_user[0].delete()
    return HTTPNoContent()


@view_config(route_name='user', request_method='POST', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(exists=False, force_own=False)
def addUser(context, request):
    """
        /people/{username}

        [RESTRICTED] Creates a system user.
    """
    username = request.matchdict['username']
    rest_params = {'username': username}

    # Initialize a User object from the request
    newuser = User()
    newuser.fromRequest(request, rest_params=rest_params)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newuser.get('_id'):
        # Already Exists
        code = 200
    else:
        # New User
        code = 201
        userid = newuser.insert()
        newuser['_id'] = userid
    handler = JSONResourceEntity(newuser.flatten(), status_code=code)
    return handler.buildResponse()
