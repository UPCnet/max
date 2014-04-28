# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPGone
from pyramid.response import Response
from bson import ObjectId

from max.models import Message
from max.decorators import MaxResponse, requirePersonActor
from max.oauth2 import oauth2


@view_config(route_name='message_image', request_method='GET')
@view_config(route_name='message_image_sizes', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getMessageImageAttachment(context, request):
    """
        Returns an image or from local repository.
    """

    activity_id = request.matchdict.get('id', '')
    message = Message()
    message.fromDatabase(ObjectId(activity_id))

    file_size = request.matchdict.get('size', 'full')
    image, mimetype = message.getImage(size=file_size)

    if image is not None:
        response = Response(image, status_int=200)
        response.content_type = mimetype
    else:
        response = HTTPGone()

    return response


@view_config(route_name='message_file_download', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getMessageFileAttachment(context, request):
    """
        Returns file from local repository.
    """

    activity_id = request.matchdict.get('id', '')
    message = Message()
    message.fromDatabase(ObjectId(activity_id))

    file_data, mimetype = message.getFile()

    if file_data is not None:
        response = Response(file_data, status_int=200)
        response.content_type = mimetype
    else:
        response = HTTPGone()

    return response
