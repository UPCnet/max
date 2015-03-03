# -*- coding: utf-8 -*-
from max.MADMax import MADMaxDB
from max.decorators import MaxResponse
from max.decorators import requirePersonActor
from max.exceptions import ObjectNotFound
from max.exceptions import ValidationError
from max.models import User
from max.oauth2 import oauth2
from max.rabbitmq import RabbitNotifications
from max.rest.ResourceHandlers import JSONResourceEntity
from max.rest.ResourceHandlers import JSONResourceRoot
from max.rest.utils import searchParams
from max.rest.utils import extractPostData

from pyramid.httpexceptions import HTTPNoContent
from pyramid.settings import asbool
from pyramid.view import view_config


@view_config(route_name='users', request_method='GET', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def getUsers(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    users = mmdb.users.search({}, flatten=1, **searchParams(request))
    handler = JSONResourceRoot(users, remaining=users.remaining)
    return handler.buildResponse()


@view_config(route_name='user', request_method='DELETE', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def deleteUser(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    username = request.matchdict.get('username')
    found_user = mmdb.users.getItemsByusername(username)
    if not found_user:
        raise ObjectNotFound("There's no user with username: %s" % username)

    found_user[0].delete()
    return HTTPNoContent()


@view_config(route_name='user', request_method='PUT', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def ModifyUser(context, request):
    """
        /people/{username}

        Modifies any user
    """
    actor = request.actor
    properties = actor.getMutablePropertiesFromRequest(request)
    actor.modifyUser(properties)
    actor.updateConversationParticipants()
    handler = JSONResourceEntity(actor.flatten())
    return handler.buildResponse()


@view_config(route_name='users', request_method='POST', restricted='Manager')
@view_config(route_name='user', request_method='POST', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(exists=False, force_own=False)
def addUser(context, request):
    """
        /people/{username}

        [RESTRICTED] Creates a system user.
    """
    username = request.matchdict.get('username', None)
    if username is None:
        params = extractPostData(request)
        username = params.get('username', None)
        if username is None:
            raise ValidationError('Missing username in request')

    rest_params = {'username': username.lower()}

    # Initialize a User object from the request
    newuser = User()
    newuser.fromRequest(request, rest_params=rest_params)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newuser.get('_id'):
        # Already Exists
        code = 200

        # Determine if we have to recreate exchanges for an existing user
        # Defaults NOT to recreate them if not specified
        create_exchanges = asbool(request.params.get('notifications', False))
        if create_exchanges:
            notifier = RabbitNotifications(request)
            notifier.add_user(username)
    else:
        # New User
        code = 201

        # Determine if we have to recreate exchanges for a new user
        # Defaults to Create them if not specified
        create_exchanges = asbool(request.params.get('notifications', True))
        userid = newuser.insert(notifications=create_exchanges)

        newuser['_id'] = userid
    handler = JSONResourceEntity(newuser.flatten(), status_code=code)
    return handler.buildResponse()


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
