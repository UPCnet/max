# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.rest import endpoint
from max.rest.ResourceHandlers import JSONResourceRoot
from max.exceptions import ValidationError
from max.rest.ResourceHandlers import JSONResourceEntity
from max.exceptions import ObjectNotFound
from pyramid.httpexceptions import HTTPNoContent
from max.MADMax import MADMaxDB
from max.rest.utils import searchParams

from max.models import Token
from max.security.permissions import list_tokens, add_token, delete_token


@endpoint(route_name='conversation_push_tokens', request_method='GET', permission=list_tokens, requires_actor=True)
def getPushTokensForConversation(tokens, request):
    """
         /conversations/{id}/tokens
         Return all relevant tokens for a given conversation
    """

    cid = request.matchdict['id']
    mmdb = MADMaxDB(request.db)
    query = {'talkingIn.id': cid}

    result = []

    users = mmdb.users.search(query, show_fields=["username"], sort_by_field="username", flatten=1)
    usernames = [user['username'] for user in users]

    tokens.search({'_owner': {'$in': [usernames]}}, **searchParams(request))

    if usernames:
        tokens.search({'_owner': {'$in': [usernames]}}, **searchParams(request))

        for token in tokens:
            result.append(dict(token=token['token'], platform=token['platform'], username=token['_owner']))

    handler = JSONResourceRoot(result)
    return handler.buildResponse()


@endpoint(route_name='context_push_tokens', request_method='GET', permission=list_tokens, requires_actor=True)
def getPushTokensForContext(tokens, request):
    """
         /contexts/{hash}/tokens
         Return all relevant tokens for a given context
    """

    cid = request.matchdict['hash']
    contexts = MADMaxCollection(request.db.contexts, query_key='hash')
    ctxt = contexts[cid]

    result = []

    users = ctxt.subscribedUsers()
    usernames = [user['username'] for user in users]

    if usernames:
        tokens.search({'_owner': {'$in': [usernames]}}, **searchParams(request))

        for token in tokens:
            result.append(dict(token=token['token'], platform=token['platform'], username=token['_owner']))

    handler = JSONResourceRoot(result)
    return handler.buildResponse()


@endpoint(route_name='tokens', request_method='POST', permission=add_token, requires_actor=True)
def addUserDevice(tokens, request):
    """ Adds a new user device linked to a user.
    """

    newtoken = Token()
    newtoken.fromRequest(request)
    newtoken.insert()

    handler = JSONResourceEntity(newtoken.flatten(), status_code=201)
    return handler.buildResponse()


@endpoint(route_name='token', request_method='DELETE', permission=delete_token, requires_actor=True)
def deleteUserDevice(token, request):
    """ Delete an existing user device .
    """
    token.delete()
    return HTTPNoContent()


@endpoint(route_name='user_tokens', request_method='DELETE', permission=delete_token, requires_actor=True)
def deleteAllUserDevices(user, request):
    """ Delete all tokens of the specified platform.
    """
    user.delete_tokens()
    return HTTPNoContent()


@endpoint(route_name='user_platform_tokens', request_method='DELETE', permission=delete_token, requires_actor=True)
def deleteUserDevicesByPlatform(user, request):
    """ Delete all tokens of the specified platform.
    """
    platform = request.matchdict['platform']
    user.delete_tokens(platform=platform)

    return HTTPNoContent()
