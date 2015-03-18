# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.decorators import MaxResponse
from max.oauth2 import oauth2
from max.rest.ResourceHandlers import JSONResourceRoot
from max.decorators import requirePersonActor
from pyramid.view import view_config
from max.exceptions import ValidationError
from max.rest.ResourceHandlers import JSONResourceEntity
from max.exceptions import ObjectNotFound
from pyramid.httpexceptions import HTTPNoContent


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


@view_config(route_name='user_device', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def addUserDevice(context, request):
    """ Adds a new user device to the user's profile.
    """
    platform = request.matchdict['platform']
    token = request.matchdict['token']
    supported_platforms = ['ios', 'android']
    if platform not in supported_platforms:
        raise ValidationError('Not supported platform.')

    if len(token) < 10:
        raise ValidationError('No valid device token.')

    actor = request.actor

    code = 201
    actor.addUserDevice(platform, token)
    handler = JSONResourceEntity(actor.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='user_device', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def deleteUserDevice(context, request):
    """ Delete an existing user device to the user's profile.
    """
    platform = request.matchdict['platform']
    token = request.matchdict['token']
    supported_platforms = ['ios', 'android']
    if platform not in supported_platforms:
        raise ValidationError('Not supported platform.')

    actor = request.actor

    if token not in actor.get(platform + 'Devices', ''):
        raise ObjectNotFound("Token not found in user's devices.")

    actor.deleteUserDevice(platform, token)

    return HTTPNoContent()


@view_config(route_name='user_platform_tokens', request_method='DELETE', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(exists=True, force_own=False)
def deleteUserDevicesByPlatform(context, request):
    """ Delete an existing user device to the user's profile.
    """
    platform = request.matchdict['platform']
    supported_platforms = ['ios', 'android']
    if platform not in supported_platforms:
        raise ValidationError('Not supported platform.')

    actor = request.actor

    actor.deleteUserDevices(platform)

    return HTTPNoContent()
