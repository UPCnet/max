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

from max.security.permissions import manage_push_tokens, view_push_tokens


@endpoint(route_name='conversation_push_tokens', request_method='GET', permission=view_push_tokens, requires_actor=True)
def getPushTokensForConversation(context, request):
    """
         /conversations/{id}/tokens
         Return all relevant tokens for a given conversation
    """

    cid = request.matchdict['id']

    mmdb = MADMaxDB(request.db)
    query = {'talkingIn.id': cid}
    users = mmdb.users.search(query, show_fields=["username", "iosDevices", "androidDevices"], sort_by_field="username", flatten=1, **searchParams(request))

    result = []
    for user in users:
        for idevice in user.get('iosDevices', []):
            result.append(dict(token=idevice, platform='iOS', username=user.get('username')))
        for adevice in user.get('androidDevices', []):
            result.append(dict(token=adevice, platform='android', username=user.get('username')))

    handler = JSONResourceRoot(result)
    return handler.buildResponse()


@endpoint(route_name='context_push_tokens', request_method='GET', permission=view_push_tokens, requires_actor=True)
def getPushTokensForContext(context, request):
    """
         /contexts/{hash}/tokens
         Return all relevant tokens for a given context
    """

    cid = request.matchdict['hash']
    contexts = MADMaxCollection(request.db.contexts, query_key='hash')
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


@endpoint(route_name='user_device', request_method='POST', permission=manage_push_tokens, requires_actor=True)
def addUserDevice(user, request):
    """ Adds a new user device to the user's profile.
    """
    platform = request.matchdict['platform']
    token = request.matchdict['token']
    supported_platforms = ['ios', 'android']
    if platform not in supported_platforms:
        raise ValidationError('Not supported platform.')

    if len(token) < 10:
        raise ValidationError('No valid device token.')

    code = 201
    user.addUserDevice(platform, token)
    handler = JSONResourceEntity(user.flatten(), status_code=code)
    return handler.buildResponse()


@endpoint(route_name='user_device', request_method='DELETE', permission=manage_push_tokens, requires_actor=True)
def deleteUserDevice(user, request):
    """ Delete an existing user device to the user's profile.
    """
    platform = request.matchdict['platform']
    token = request.matchdict['token']
    supported_platforms = ['ios', 'android']
    if platform not in supported_platforms:
        raise ValidationError('Not supported platform.')

    if token not in user.get(platform + 'Devices', ''):
        raise ObjectNotFound("Token not found in user's devices.")

    user.deleteUserDevice(platform, token)

    return HTTPNoContent()


@endpoint(route_name='user_platform_tokens', request_method='DELETE', permission=manage_push_tokens, requires_actor=True)
def deleteUserDevicesByPlatform(user, request):
    """ Delete an existing user device to the user's profile.
    """
    platform = request.matchdict['platform']
    supported_platforms = ['ios', 'android']
    if platform not in supported_platforms:
        raise ValidationError('Not supported platform.')

    user.deleteUserDevices(platform)

    return HTTPNoContent()
