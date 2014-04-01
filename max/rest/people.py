# -*- coding: utf-8 -*-
import os
from pymongo import DESCENDING
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented
from pyramid.httpexceptions import HTTPNoContent
from pyramid.response import Response

from max.exceptions import Unauthorized
from max.exceptions import ValidationError
from max.exceptions import ObjectNotFound
from max.oauth2 import oauth2
from max.MADMax import MADMaxDB
from max.models import User
from max.rest.utils import searchParams, flatten
from max.decorators import MaxResponse, requirePersonActor
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity

from PIL import Image


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
    users = mmdb.users.search(query, show_fields=["username", "displayName", "objectType", 'subscribedTo'], sort="username", flatten=0, **searchParams(request))
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
    actor = request.actor.flatten()

    # Flattened actor will contain only the visible fields for the current user
    # So we will only prepare the calculated conversations  (lastMessage & displayName)
    # if we have permission to view the talkingIn field
    if request.actor.check_field_permission('talkingIn', 'view'):
        actor.setdefault('talkingIn', [])
        mmdb = MADMaxDB(context.db)
        for conversation in actor['talkingIn']:
            query = {'objectType': 'message',
                     'contexts.id': conversation['id']
                     }

            # In two people conversations, force displayName to the displayName of
            # the partner in the conversation
            if 'group' not in conversation.get('tags', []):
                partner = [user for user in conversation['participants'] if user["username"] != request.actor.username][0]
                conversation['displayName'] = partner["displayName"]

            messages = mmdb.messages.search(query, flatten=1, limit=1, sort="published", sort_dir=DESCENDING)
            lastMessage = messages[0]
            conversation['lastMessage'] = {'published': lastMessage['published'],
                                           'content': lastMessage['object']['content']
                                           }
            conversation['messages'] = 0

        actor['talkingIn'] = sorted(actor['talkingIn'], reverse=True, key=lambda conv: conv['lastMessage']['published'])

    handler = JSONResourceEntity(actor)
    return handler.buildResponse()


@view_config(route_name='user', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(exists=False)
def addOwnUser(context, request):
    """
        /people/{username}

        Creates a the own system user.
    """
    username = request.matchdict['username'].lower()
    rest_params = {'username': username}

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
    else:
        # New User
        code = 201
        userid = newuser.insert()
        newuser['_id'] = userid
    handler = JSONResourceEntity(newuser.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='avatar', request_method='GET')
@view_config(route_name='avatar_sizes', request_method='GET')
def getUserAvatar(context, request):
    """
        /people/{username}/avatar

        Returns user avatar. Public endpoint.
    """

    AVATAR_FOLDER = request.registry.settings.get('avatar_folder')
    username = request.matchdict['username']

    def exists(filename):
        return os.path.exists(os.path.join(AVATAR_FOLDER, filename))

    named_size = request.matchdict.get('size', None)
    filename = 'missing.png'

    # Check if the named size exists, otherwise fallback to normal size checks
    if named_size:
        named_size_image_filename = '{}-{}.png'.format(username, named_size)
        if exists(named_size_image_filename):
            filename = named_size_image_filename
        else:
            named_size = None

    # Check if normal size exists, otherwise, fallback to
    # previously setted missing avatar image filename
    normal_filename = '{}.png'.format(username)
    if named_size is None and exists(normal_filename):
        filename = '{}.png'.format(username)

    data = open(os.path.join(AVATAR_FOLDER, filename)).read()
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
    AVATAR_FOLDER = request.registry.settings.get('avatar_folder')
    if not os.path.exists(AVATAR_FOLDER):
        os.mkdir(AVATAR_FOLDER)
    username = request.matchdict['username']

    if request.content_type != 'multipart/form-data' and \
       len(request.POST.keys()) != 1:
        raise ValidationError('Not supported upload method.')

    file_key = request.POST.keys()[0]
    input_file = request.POST[file_key].file
    # original_filename = request.POST[file_key].filename
    destination_filename = '{}.png'.format(username)
    destination_large_filename = '{}-large.png'.format(username)

    # Saving the standard (48x48) avatar image in png format, resize if needed
    file_path = os.path.join(AVATAR_FOLDER, destination_filename)
    input_file.seek(0)
    image = Image.open(input_file)

    if image.size[0] > 48:
        image.thumbnail((48,9800), Image.ANTIALIAS)
        image = image.transform((48,48), Image.EXTENT, (0, 0, 48, 48), Image.BICUBIC)
    image.save(file_path)

    # Saving the large (176x176) avatar image in png format, resize if needed
    file_path = os.path.join(AVATAR_FOLDER, destination_large_filename)
    input_file.seek(0)
    image = Image.open(input_file)

    if image.size[0] > 176:
        image.thumbnail((176,9800), Image.ANTIALIAS)
        image = image.transform((176,176), Image.EXTENT, (0, 0, 176, 176), Image.BICUBIC)
    image.save(file_path)

    # Use with files
    # with open(file_path, 'wb') as output_file:
    #     shutil.copyfileobj(input_file, output_file)

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
