# -*- coding: utf-8 -*-
from pyramid.view import view_config

from max.decorators import MaxResponse
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot


@view_config(route_name='admin_security', request_method='GET')
@MaxResponse
def getSecurity(context, request):
    """
         /admin/security

         Expose the current MAX security roles and its members

         It's intended to be a protected by IP endpoint as we do not want
         eavesdroping on this information
    """
    mmdb = MADMaxDB(context.db)
    query = {}
    roles = mmdb.security.search(query, flatten=1)

    handler = JSONResourceRoot(roles)
    return handler.buildResponse()
