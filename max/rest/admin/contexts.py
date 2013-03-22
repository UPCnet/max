# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent

from max.oauth2 import oauth2, restricted
from max.decorators import MaxResponse
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot
from max.exceptions import ObjectNotFound


@view_config(route_name='admin_contexts', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@restricted(['Manager'])
def getContexts(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    contexts = mmdb.contexts.dump(flatten=1)
    handler = JSONResourceRoot(contexts)
    return handler.buildResponse()


@view_config(route_name='admin_context', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
@restricted(['Manager'])
def deleteContext(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    contextid = request.matchdict.get('id', None)
    try:
        found_context = mmdb.contexts[contextid]
    except:
        raise ObjectNotFound("There's no context with id: %s" % contextid)

    found_context.delete()

    # XXX in admin too ?
    #found_context[0].removeUserSubscriptions()
    return HTTPNoContent()
