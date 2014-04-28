# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPGone
from pyramid.response import Response

from max.MADMax import MADMaxDB
from max.decorators import MaxResponse, requirePersonActor
from max.oauth2 import oauth2
from max.exceptions import Unauthorized

import os
import re


@view_config(route_name='message_image', request_method='GET')
@view_config(route_name='message_image_sizes', request_method='GET')
@view_config(route_name='message_file_download', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getActivityImageOrFile(context, request):
    """

        Returns an image or file from local repository.
    """
    mmdb = MADMaxDB(context.db)
    resource_root, resource_identifier = re.search(r'^/(\w+)/\{(\w+)\}.*$', request.matched_route.path).groups()
    activity_id = request.matchdict.get(resource_identifier, '')
    collection = mmdb.messages
    collection_item_storage = 'talkingIn'
    collection_item_key = 'id'

    # Full images get no extension
    file_size = request.matchdict.get('size', 'full')
    file_extension = '.{}'.format(file_size) if file_size != 'full' else ''

    found_activity = collection[activity_id]

    if found_activity.get('contexts', []):
        readable_contexts_urls = [a[collection_item_key] for a in request.actor[collection_item_storage] if 'read' in a['permissions']]

        can_read = False
        for context in found_activity['contexts']:
            if context[collection_item_key] in readable_contexts_urls:
                can_read = True
    else:
        # Sure ??? Do we have to check if the activity is ours, or from a followed user?
        # Try to unify this criteria with the criteria used in geting the timeline activities
        can_read = True

    if not can_read:
        raise Unauthorized("You are not allowed to read this activity: %s" % activity_id)

    base_path = request.registry.settings.get('file_repository')

    dirs = list(re.search('(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{2})(\w{12})', activity_id).groups())
    filename = dirs.pop() + file_extension

    path = base_path + '/' + '/'.join(dirs)

    if os.path.exists(os.path.join(path, filename)):
        data = open(os.path.join(path, filename)).read()
        image = Response(data, status_int=200)
        # TODO: Look if mimetype is setted, and if otherwise, treat it conveniently
        image.content_type = 'image/jpeg' if file_size != 'full' else str(found_activity['object'].get('mimetype', 'image/jpeg'))
        return image

    return HTTPGone()
