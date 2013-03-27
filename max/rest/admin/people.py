# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent

from max.oauth2 import oauth2
from max.decorators import MaxResponse
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot
from max.exceptions import ObjectNotFound


@view_config(route_name='users', request_method='GET', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def getUsers(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    users = mmdb.users.dump(flatten=1)
    handler = JSONResourceRoot(users)
    return handler.buildResponse()


@view_config(route_name='user', request_method='DELETE', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def deleteUser(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    userid = request.matchdict.get('id', None)
    try:
        found_user = mmdb.users[userid]
    except:
        raise ObjectNotFound("There's no user with id: %s" % userid)

    found_user.delete()
    return HTTPNoContent()
