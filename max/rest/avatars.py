# -*- coding: utf-8 -*-
from max.MADMax import MADMaxDB
from max.exceptions import ObjectNotFound
from max.rest.utils import download_twitter_user_image
from max.rest.utils import get_avatar_folder
from max.rest.utils import get_twitter_api

from pyramid.response import Response
from pyramid.view import view_config

import os
import time


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
