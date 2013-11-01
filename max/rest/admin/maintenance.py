# -*- coding: utf-8 -*-
from pyramid.view import view_config

from max.oauth2 import oauth2
from max.exceptions import ObjectNotFound, ValidationError
from max.decorators import MaxResponse, requirePersonActor

from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot


@view_config(route_name='maintenance_keywords', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False, exists=False)
def rebuildKeywords(context, request):
    """
         /maintenance/keywords

         Rebuild keywords of all activities

    """
    mmdb = MADMaxDB(context.db)
    activities = mmdb.activity.dump()
    for activity in activities:
        activity.object.setKeywords()
        activity.setKeywords()
        activity.save()

    handler = JSONResourceRoot([])
    return handler.buildResponse()
