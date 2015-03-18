# -*- coding: utf-8 -*-
from max.MADMax import MADMaxDB
from max.exceptions import ObjectNotFound
from max.rest.utils import download_twitter_user_image
from max.rest.utils import get_avatar_folder
from max.rest.utils import get_twitter_api

from pyramid.response import Response
from pyramid.view import view_config
from max.decorators import MaxResponse
import os
import time

from PIL import Image
from PIL import ImageOps

from max.oauth2 import oauth2
from max.decorators import requirePersonActor

from max.exceptions import ValidationError

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


@view_config(route_name='context_avatar', request_method='GET')
def getContextAvatar(context, request):
    """
        /contexts/{hash}/avatar

        Return the context's avatar. To the date, this is only implemented to
        work integrated with Twitter.
    """
    chash = request.matchdict['hash']

    base_folder = request.registry.settings.get('avatar_folder')
    avatar_folder = get_avatar_folder(base_folder, 'contexts', chash)

    context_image_filename = '%s/%s' % (avatar_folder, chash)

    api = get_twitter_api(request.registry)
    if not os.path.exists(context_image_filename):
        mmdb = MADMaxDB(context.db)
        found_context = mmdb.contexts.getItemsByhash(chash)
        if len(found_context) > 0:
            twitter_username = found_context[0]['twitterUsername']
            download_twitter_user_image(api, twitter_username, context_image_filename)
        else:
            raise ObjectNotFound("There's no context with hash %s" % chash)

    if os.path.exists(context_image_filename):
        # Calculate time since last download and set if we have to re-download or not
        modification_time = os.path.getmtime(context_image_filename)
        hours_since_last_modification = (time.time() - modification_time) / 60 / 60
        if hours_since_last_modification > 3:
            mmdb = MADMaxDB(context.db)
            found_context = mmdb.contexts.getItemsByhash(chash)
            twitter_username = found_context[0]['twitterUsername']
            download_twitter_user_image(api, twitter_username, context_image_filename)
    else:
        context_image_filename = '{}/missing-context.png'.format(base_folder)

    data = open(context_image_filename).read()
    image = Response(data, status_int=200)
    image.content_type = 'image/png'
    return image
