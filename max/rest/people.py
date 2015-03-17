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
from max.rest.utils import get_avatar_folder
from max.rest.utils import flatten
from max.rest.utils import searchParams
from max.rest.utils import extractPostData

from pyramid.httpexceptions import HTTPNoContent
from pyramid.httpexceptions import HTTPNotImplemented
from pyramid.response import Response
from pyramid.settings import asbool
from pyramid.view import view_config

from PIL import Image
from PIL import ImageOps

import os


@view_config(route_name='users', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getUsers(context, request):
    """
         /people

         Return the result of a query specified by the username param as
         a list of usernames. For UI use only.
    """
    mmdb = MADMaxDB(context.db)
    query = {}
    users = mmdb.users.search(query, show_fields=["username", "displayName", "objectType", 'subscribedTo'], sort_by_field="username", flatten=0, **searchParams(request))
    remaining = users.remaining

    # Filter user results

    users = [user for user in users if request.actor.isAllowedToSee(user)]
    handler = JSONResourceRoot(flatten(users, squash=['subscribedTo']), remaining=remaining)
    return handler.buildResponse()


@view_config(route_name='user', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False)
def getUser(context, request):
    """
        /people/{username}

        Return the required user object.
    """

    # Flattened actor will contain only the visible fields for the current user
    # So we will only prepare the calculated conversations  (lastMessage & displayName)
    # if we have permission to view the talkingIn field

    actor_info = request.actor.getInfo()

    handler = JSONResourceEntity(actor_info)
    return handler.buildResponse()


# @view_config(route_name='users', request_method='POST')
# @view_config(route_name='user', request_method='POST')
# @MaxResponse
# @oauth2(['widgetcli'])
# @requirePersonActor(exists=False)
# def addOwnUser(context, request):
#     """
#         /people/{username}

#         Creates a the own system user.
#     """
#     username = request.matchdict.get('username', None)
#     if username is None:
#         params = extractPostData(request)
#         username = params.get('username', None)
#         if username is None:
#             raise ValidationError('Missing username in request')

#     rest_params = {'username': username.lower()}

#     # Initialize a User object from the request
#     newuser = User()
#     newuser.fromRequest(request, rest_params=rest_params)

#     # If we have the _id setted, then the object already existed in the DB,
#     # otherwise, proceed to insert it into the DB
#     # In both cases, respond with the JSON of the object and the appropiate
#     # HTTP Status Code

#     if newuser.get('_id'):
#         # Already Exists
#         code = 200

#         # Determine if we have to recreate exchanges for an existing user
#         # Defaults NOT to recreate them if not specified
#         create_exchanges = asbool(request.params.get('notifications', False))
#         if create_exchanges:
#             notifier = RabbitNotifications(request)
#             notifier.add_user(username)
#     else:
#         # New User
#         code = 201

#         # Determine if we have to recreate exchanges for a new user
#         # Defaults to Create them if not specified
#         create_exchanges = asbool(request.params.get('notifications', True))
#         userid = newuser.insert(notifications=create_exchanges)

#         newuser['_id'] = userid
#     handler = JSONResourceEntity(newuser.flatten(), status_code=code)
#     return handler.buildResponse()


@view_config(route_name='avatar', request_method='GET')
@view_config(route_name='avatar_sizes', request_method='GET')
@MaxResponse
def getUserAvatar(context, request):
    """
        /people/{username}/avatar

        Returns user avatar. Public endpoint.
    """
    base_folder = request.registry.settings.get('avatar_folder')
    username = request.matchdict['username']
    named_size = request.matchdict.get('size', '')
    filename = ''

    # First attempt to find an existing named size avatar
    # If image is not sized, this will fallback to regular avatar.
    avatar_folder = get_avatar_folder(base_folder, 'people', username, size=named_size)
    if os.path.exists(os.path.join(avatar_folder, username)):
        filename = username

    # If we were loking for a named size avatar, reaching here
    # menans we did not found it, so fallback to base avatar
    elif named_size:
        avatar_folder = get_avatar_folder(base_folder, 'people', username)
        if os.path.exists(os.path.join(avatar_folder, username)):
            filename = username

    # At this point we should have a filename set, if not, it means that we
    # couldn't locate any size of the requested avatar. In this case, set the
    # missing avatar filename, based on context and size and located at root
    # avatars folder

    avatar_folder = avatar_folder if filename else get_avatar_folder(base_folder)
    named_size_sufix = '-{}'.format(named_size) if named_size else ''
    filename = filename if filename else 'missing-people.png'.format(context, named_size_sufix)

    data = open(os.path.join(avatar_folder, filename)).read()
    image = Response(data, status_int=200)
    image.content_type = 'image/png'
    return image


@view_config(route_name='avatar', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def postUserAvatar(context, request):
    """
        /people/{username}/avatar

        Upload user avatar.
    """
    base_folder = request.registry.settings.get('avatar_folder')
    AVATAR_SIZE = (48, 48)
    LARGE_SIZE = (250, 250)

    username = request.matchdict['username']

    if request.content_type != 'multipart/form-data' and \
       len(request.POST.keys()) != 1:
        raise ValidationError('Not supported upload method.')

    file_key = request.POST.keys()[0]
    input_file = request.POST[file_key].file

    # Saving the standard avatar image in png format, resize if needed
    regular_avatar_folder = get_avatar_folder(base_folder, 'people', username)
    file_path = os.path.join(regular_avatar_folder, username)
    input_file.seek(0)
    image = Image.open(input_file)

    avatar = ImageOps.fit(image, AVATAR_SIZE, method=Image.ANTIALIAS, centering=(0, 0))
    avatar.save(file_path, 'PNG')

    # Saving the large avatar image in png format, resize if needed
    large_avatar_folder = get_avatar_folder(base_folder, 'people', username, size='large')
    file_path = os.path.join(large_avatar_folder, username)
    input_file.seek(0)
    image = Image.open(input_file)

    medium = ImageOps.fit(image, LARGE_SIZE, method=Image.ANTIALIAS, centering=(0, 0))
    medium.save(file_path, 'PNG')

    return Response("Uploaded", status_int=201)


@view_config(route_name='user', request_method='PUT')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def ModifyUser(context, request):
    """
        /people/{username}

        Modifies a system user via oauth, so only the user can modify its own
        properties.
    """
    actor = request.actor
    properties = actor.getMutablePropertiesFromRequest(request)
    actor.modifyUser(properties)
    actor.updateConversationParticipants()
    handler = JSONResourceEntity(actor.flatten())
    return handler.buildResponse()


@view_config(route_name='user', request_method='DELETE')
def DeleteUser(context, request):
    """
        User auto-deletion
    """
    return HTTPNotImplemented()  # pragma: no cover


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
