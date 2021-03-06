# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.models import Token
from max.rest import JSONResourceEntity
from max.rest import JSONResourceRoot
from max.rest import endpoint
from max.utils import searchParams
from max.security.permissions import add_token
from max.security.permissions import delete_token
from max.security.permissions import list_tokens

from pyramid.httpexceptions import HTTPNoContent


def formatted_tokens(tokens):
    for token in tokens:
        yield dict(token=token['token'], platform=token['platform'], username=token['_owner'])


@endpoint(route_name='conversation_push_tokens', request_method='GET', permission=list_tokens)
def getPushTokensForConversation(tokens, request):
    """
        Return conversation tokens
    """
    cid = request.matchdict['id']
    query = {'talkingIn.id': cid}

    user_tokens = []
    users = request.db.users.search(query, show_fields=["username"], sort_by_field="username", flatten=1)
    usernames = [user['username'] for user in users]

    if usernames:
        # Modifico el limit a -1 para que me devuelva todos los usuarios de la mongo no solo el limite de 10
        # user_tokens = tokens.search({'_owner': {'$in': usernames}}, **searchParams(request))
        user_tokens = tokens.search({'_owner': {'$in': usernames}}, {'limit': -1})

    handler = JSONResourceRoot(request, formatted_tokens(user_tokens))
    return handler.buildResponse()


@endpoint(route_name='context_push_tokens', request_method='GET', permission=list_tokens)
def getPushTokensForContext(tokens, request):
    """
         Return context tokens
    """

    cid = request.matchdict['hash']
    contexts = MADMaxCollection(request, 'contexts', query_key='hash')
    ctxt = contexts[cid]

    user_tokens = []
    users = ctxt.subscribedUsers()
    users_unsubscribepush = ctxt.unSubscribedPushUsers()
    usernames = [user['username'] for user in users]
    usernames_unsubscribepush= [user['username'] for user in users_unsubscribepush]
    usernames_to_notify = [e for e in usernames if e not in usernames_unsubscribepush]

    if usernames_to_notify:
        # Modifico el limit a -1 para que me devuelva todos los usuarios de la mongo no solo el limite de 10
        # user_tokens = tokens.search({'_owner': {'$in': usernames}}, **searchParams(request))
        user_tokens = tokens.search({'_owner': {'$in': usernames_to_notify}}, {'limit': -1})

    handler = JSONResourceRoot(request, formatted_tokens(user_tokens))
    return handler.buildResponse()


@endpoint(route_name='tokens', request_method='POST', permission=add_token)
def add_device_token(tokens, request):
    """
        Adds a user device token

        Adds a new user device linked to a user. If the token already exists for any user, we'll assume that the new
        user is using the old user's device, so we'll delete all the previous tokens and replace them with the new one.

        16/07/2018 Si este WS nos devuelve un 404 y no entra, es que no tenemos en el nginx del max el /tokens
                   la nueva APP Utalk lo utiliza
                   la antigua utiliza el fix_deprecated_add_token
                   POST /people/{username}/device/{platform}/{token}
    """
    newtoken = Token.from_request(request)

    if '_id' in newtoken:
        newtoken.delete()
        newtoken = Token.from_request(request)

    # insert the token always
    newtoken.insert()

    handler = JSONResourceEntity(request, newtoken.flatten(), status_code=201)
    return handler.buildResponse()


@endpoint(route_name='user_tokens', request_method='GET', permission=list_tokens)
def view_user_tokens(user, request):
    """
        Delete all platform tokens
    """
    tokens = user.get_tokens()
    handler = JSONResourceRoot(request, tokens)
    return handler.buildResponse()


@endpoint(route_name='user_platform_tokens', request_method='GET', permission=list_tokens)
def view_platform_user_tokens(user, request):
    """
        Get all user tokens for platform
    """
    platform = request.matchdict['platform']
    tokens = user.get_tokens(platform)
    handler = JSONResourceRoot(request, tokens)
    return handler.buildResponse()


@endpoint(route_name='token', request_method='DELETE', permission=delete_token)
def deleteUserDevice(token, request):
    """
        Delete user device token

        16/07/2018 Si este WS nos devuelve un 404 y no entra, es que no tenemos en el nginx del max el /tokens
                   la nueva APP Utalk lo utiliza
                   la antigua utiliza el fix_deprecated_add_token
                   POST /people/{username}/device/{platform}/{token}
    """
    token.delete()
    return HTTPNoContent()


@endpoint(route_name='user_tokens', request_method='DELETE', permission=delete_token)
def deleteAllUserDevices(user, request):
    """
        Delete all user device tokens
    """
    user.delete_tokens()
    return HTTPNoContent()


@endpoint(route_name='user_platform_tokens', request_method='DELETE', permission=delete_token)
def deleteUserDevicesByPlatform(user, request):
    """
        Delete all user device tokens for platform
    """
    platform = request.matchdict['platform']
    user.delete_tokens(platform=platform)

    return HTTPNoContent()
