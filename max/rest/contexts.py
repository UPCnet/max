# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented
from pyramid.response import Response

from max.MADMax import MADMaxDB
from max.oauth2 import oauth2
from max.decorators import MaxResponse, requirePersonActor
from max.rest.ResourceHandlers import JSONResourceRoot
import os

from max.rest.utils import downloadTwitterUserImage
import time


@view_config(route_name='public_contexts', request_method='GET')
@MaxResponse
@requirePersonActor(force_own=False)
@oauth2(['widgetcli'])
def getPublicContexts(context, request):
    """
        /contexts/public

        Return a list of public-subscribable contexts
    """
    mmdb = MADMaxDB(context.db)
    found_contexts = mmdb.contexts.search({'permissions.subscribe': 'public'}, flatten=1)

    handler = JSONResourceRoot(found_contexts)
    return handler.buildResponse()


@view_config(route_name='context_avatar', request_method='GET')
def getContextAvatar(context, request):
    """
        /contexts/{hash}/avatar

        Return the context's avatar. To the date, this is only implemented to
        work integrated with Twitter.
    """
    chash = request.matchdict['hash']
    AVATAR_FOLDER = request.registry.settings.get('avatar_folder')
    context_image_filename = '%s/%s.jpg' % (AVATAR_FOLDER, chash)

    if not os.path.exists(context_image_filename):
        mmdb = MADMaxDB(context.db)
        found_context = mmdb.contexts.getItemsByhash(chash)
        if len(found_context) > 0:
            twitter_username = found_context[0]['twitterUsername']
            downloadTwitterUserImage(twitter_username, context_image_filename)

    if os.path.exists(context_image_filename):
        # Calculate time since last download and set if we have to redownload or not
        modification_time = os.path.getmtime(context_image_filename)
        hours_since_last_modification = (time.time() - modification_time) / 60 / 60
        if hours_since_last_modification > 3:
            mmdb = MADMaxDB(context.db)
            found_context = mmdb.contexts.getItemsByhash(chash)
            twitter_username = found_context[0]['twitterUsername']
            downloadTwitterUserImage(twitter_username, context_image_filename)
    else:
        context_image_filename = '%s/missing.jpg' % (AVATAR_FOLDER)

    data = open(context_image_filename).read()
    image = Response(data, status_int=200)
    image.content_type = 'image/jpeg'
    return image


@view_config(route_name='context', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
def DeleteContext(context, request):
    """
    """
    return HTTPNotImplemented
