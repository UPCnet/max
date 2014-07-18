# -*- coding: utf-8 -*-
from max.decorators import MaxResponse
from max.decorators import requirePersonActor
from max.models import Message
from max.oauth2 import oauth2

from pyramid.httpexceptions import HTTPGone
from pyramid.response import Response
from pyramid.view import view_config

from base64 import b64encode
from bson import ObjectId


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
        if request.headers.get('content-type', '') == 'application/base64':
            image = b64encode(image)
            mimetype = 'application/base64'

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
    message_id = request.matchdict.get('id', '')
    message = Message()
    message.fromDatabase(ObjectId(message_id))

    file_data, mimetype = message.getFile()

    if file_data is not None:
        response = Response(file_data, status_int=200)
        response.content_type = mimetype
        filename = message['object'].get('filename', message_id)
        response.headers.add('Content-Disposition', 'attachment; filename={}'.format(filename))
    else:
        response = HTTPGone()

    return response
