# -*- coding: utf-8 -*-
from pyramid.view import view_config
from max.rest.utils import searchParams

from max.MADMax import MADMaxDB, MADMaxCollection
from max.decorators import MaxResponse
from max.oauth2 import oauth2
from max.rest.ResourceHandlers import JSONResourceRoot


@view_config(route_name='pushtokens', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
def getPushTokensForConversation(context, request):
    """
         /conversations/{id}/tokens
         Return all relevant tokens for a given conversation
    """

    cid = request.matchdict['id']
    conversations = MADMaxCollection(context.db.conversations)
    conversation = conversations[cid]

    mmdb = MADMaxDB(context.db)
    query = {"username": {"$in": conversation['participants']}}
    users = mmdb.users.search(query, show_fields=["username", "iosDevices", "androidDevices"], sort="username", flatten=1, **searchParams(request))

    result = []
    for user in users:
        for idevice in user.get('iosDevices', []):
            result.append(dict(token=idevice, platform='iOS', username=user.get('username')))
        for adevice in user.get('androidDevices', []):
            result.append(dict(token=idevice, platform='android', username=user.get('username')))

    handler = JSONResourceRoot(result)
    return handler.buildResponse()
