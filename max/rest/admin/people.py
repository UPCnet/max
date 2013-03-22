# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent

from max.oauth2 import oauth2, restricted
from max.decorators import MaxResponse
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot
from max.exceptions import ObjectNotFound


@view_config(route_name='admin_users', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@restricted(['Manager'])
def getUsers(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    users = mmdb.users.dump(flatten=1)
    handler = JSONResourceRoot(users)
    return handler.buildResponse()


@view_config(route_name='admin_user', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
@restricted(['Manager'])
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
