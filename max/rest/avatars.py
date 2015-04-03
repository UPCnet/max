# -*- coding: utf-8 -*-
from max.exceptions import ValidationError
from max.rest import endpoint
from max.utils.twitter import download_twitter_user_image
from max.utils.image import get_avatar_folder
from max.utils.twitter import get_twitter_api
from max.security.permissions import modify_avatar

from pyramid.response import Response

from PIL import Image
from PIL import ImageOps

import os
import time


@endpoint(route_name='avatar', request_method='POST', requires_actor=True, permission=modify_avatar)
def postUserAvatar(user, request):
    """
        Upload user avatar
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


@endpoint(route_name='avatar', request_method='GET')
@endpoint(route_name='avatar_sizes', request_method='GET')
def getUserAvatar(context, request):
    """
        Get user avatar
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


@endpoint(route_name='context_avatar', request_method='GET')
def getContextAvatar(context, request):
    """
        Get context avatar

        To the date, this is only implemented to
        work integrated with Twitter.
    """
    chash = context['hash']
    twitter_username = context['twitterUsername']

    base_folder = request.registry.settings.get('avatar_folder')
    avatar_folder = get_avatar_folder(base_folder, 'contexts', chash)

    context_image_filename = '%s/%s' % (avatar_folder, chash)

    api = get_twitter_api(request.registry)
    if not os.path.exists(context_image_filename):
        download_twitter_user_image(api, twitter_username, context_image_filename)

    if os.path.exists(context_image_filename):
        # Calculate time since last download and set if we have to re-download or not
        modification_time = os.path.getmtime(context_image_filename)
        hours_since_last_modification = (time.time() - modification_time) / 60 / 60
        if hours_since_last_modification > 3:
            download_twitter_user_image(api, twitter_username, context_image_filename)
    else:
        context_image_filename = '{}/missing-context.png'.format(base_folder)

    data = open(context_image_filename).read()
    image = Response(data, status_int=200)
    image.content_type = 'image/png'
    return image


@endpoint(route_name='conversation_avatar', request_method='GET')
def getConversationUserAvatar(conversation, request):
    """
        Get conversation avatar

        Returns conversation avatar. Public endpoint.
    """
    cid = request.matchdict['id']

    base_folder = request.registry.settings.get('avatar_folder')
    avatar_folder = get_avatar_folder('conversations', cid)

    missing_avatar = os.path.join(base_folder, 'missing-conversation.png')
    conversation_avatar = os.path.join(avatar_folder, cid)
    filename = conversation_avatar if os.path.exists(conversation_avatar) else missing_avatar

    data = open(filename).read()
    image = Response(data, status_int=200)
    image.content_type = 'image/png'
    return image
