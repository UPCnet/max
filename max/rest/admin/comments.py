# -*- coding: utf-8 -*-
from pyramid.view import view_config

from max.oauth2 import oauth2
from max.decorators import MaxResponse
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot
from max.rest.utils import searchParams


@view_config(route_name='comments', request_method='GET', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def getGlobalComments(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    is_head = request.method == 'HEAD'
    activities = mmdb.activity.search({'verb': 'comment'}, flatten=1, count=is_head, **searchParams(request))
    handler = JSONResourceRoot(activities, stats=is_head)
    return handler.buildResponse()
