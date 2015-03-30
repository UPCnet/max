# -*- coding: utf-8 -*-
from max.models import Message

from pyramid.httpexceptions import HTTPGone
from pyramid.response import Response
from max.rest import endpoint
from max.rest.utils import searchParams, flatten
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceEntity, JSONResourceRoot
from base64 import b64encode
from bson import ObjectId

from max.security.permissions import view_messages, view_message, add_message


@endpoint(route_name='messages', request_method='GET', requires_actor=True, permission=view_messages)
def getMessages(conversation, request):
    """
         /conversations/{id}/messages
         Return all messages from a conversation
    """
    mmdb = MADMaxDB(request.db)
    query = {'contexts.id': conversation['_id']}
    messages = mmdb.messages.search(query, sort_by_field="published", keep_private_fields=False, **searchParams(request))
    remaining = messages.remaining
    handler = JSONResourceRoot(flatten(messages[::-1]), remaining=remaining)
    return handler.buildResponse()


@endpoint(route_name='user_conversation_messages', request_method='POST', requires_actor=True, permission=add_message)
@endpoint(route_name='messages', request_method='POST', requires_actor=True, permission=add_message)
def add_message(conversation, request):
    """
         Adds a message to a conversation. The request.actor is the one "talking", either
         if it was the authenticated user, the rest username or the post body actor, in this order.
    """
    message_params = {'actor': request.actor,
                      'verb': 'post',
                      'contexts': [{'objectType': 'conversation',
                                    'id': conversation['_id']
                                    }]
                      }

    # Initialize a Message (Activity) object from the request
    newmessage = Message()
    newmessage.fromRequest(request, rest_params=message_params)

    if newmessage['object']['objectType'] == u'image' or \
       newmessage['object']['objectType'] == u'file':
        # Extract the file before saving object
        message_file = newmessage.extract_file_from_activity()
        message_oid = newmessage.insert()
        newmessage['_id'] = ObjectId(message_oid)
        newmessage.process_file(request, message_file)
        newmessage.save()
    else:
        message_oid = newmessage.insert()
        newmessage['_id'] = message_oid

    handler = JSONResourceEntity(newmessage.flatten(), status_code=201)
    return handler.buildResponse()


@endpoint(route_name='message_image', request_method='GET', requires_actor=True, permission=view_message)
@endpoint(route_name='message_image_sizes', request_method='GET', requires_actor=True, permission=view_message)
def getMessageImageAttachment(message, request):
    """
        Returns an image or from local repository.
    """
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


@endpoint(route_name='message_file_download', request_method='GET', requires_actor=True, permission=view_message)
def getMessageFileAttachment(message, request):
    """
        Returns file from local repository.
    """
    file_data, mimetype = message.getFile()

    if file_data is not None:
        response = Response(file_data, status_int=200)
        response.content_type = mimetype
        filename = message['object'].get('filename', message['_id'])
        response.headers.add('Content-Disposition', 'attachment; filename={}'.format(filename))
    else:
        response = HTTPGone()

    return response
