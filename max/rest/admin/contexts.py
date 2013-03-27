# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent

from max.oauth2 import oauth2
from max.decorators import MaxResponse
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot
from max.exceptions import ObjectNotFound


@view_config(route_name='contexts', request_method='GET', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def getContexts(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    contexts = mmdb.contexts.dump(flatten=1)
    handler = JSONResourceRoot(contexts)
    return handler.buildResponse()


@view_config(route_name='context', request_method='DELETE', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def DeleteContext(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    chash = request.matchdict.get('hash', None)
    found_contexts = mmdb.contexts.getItemsByhash(chash)

    if not found_contexts:
        raise ObjectNotFound("There's no context matching this url hash: %s" % chash)

    ctx = found_contexts[0]
    ctx.removeUserSubscriptions()
    ctx.removeActivities(logical=True)
    ctx.delete()
    return HTTPNoContent()
