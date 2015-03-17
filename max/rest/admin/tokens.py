# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.decorators import MaxResponse
from max.oauth2 import oauth2
from max.rest.ResourceHandlers import JSONResourceRoot

from pyramid.view import view_config


@view_config(route_name='context_push_tokens', request_method='GET', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def getPushTokensForContext(context, request):
    """
         /contexts/{hash}/tokens
         Return all relevant tokens for a given context
    """

    cid = request.matchdict['hash']
    contexts = MADMaxCollection(context.db.contexts, query_key='hash')
    ctxt = contexts[cid]

    users = ctxt.subscribedUsers()

    result = []
    for user in users:
        for idevice in user.get('iosDevices', []):
            result.append(dict(token=idevice, platform='iOS', username=user.get('username')))
        for adevice in user.get('androidDevices', []):
            result.append(dict(token=adevice, platform='android', username=user.get('username')))

    handler = JSONResourceRoot(result)
    return handler.buildResponse()
