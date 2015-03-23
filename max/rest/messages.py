# -*- coding: utf-8 -*-
from max.models import Message

from pyramid.httpexceptions import HTTPGone
from pyramid.response import Response
from max.rest import endpoint
from max.exceptions import Unauthorized
from max.rest.utils import searchParams, flatten
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceEntity, JSONResourceRoot
from base64 import b64encode
from bson import ObjectId


@endpoint(route_name='messages', request_method='GET', requires_actor=True)
def getMessages(context, request):
    """
         /conversations/{id}/messages
         Return all messages from a conversation
    """
    cid = request.matchdict['id']
    if cid not in [ctxt.get("id", '') for ctxt in request.actor.talkingIn]:
        raise Unauthorized('User {} is not allowed to view this conversation'.format(request.actor.username))

    mmdb = MADMaxDB(request.db)
    query = {'contexts.id': cid}
    messages = mmdb.messages.search(query, sort_by_field="published", keep_private_fields=False, **searchParams(request))
    remaining = messages.remaining
    handler = JSONResourceRoot(flatten(messages[::-1]), remaining=remaining)
    return handler.buildResponse()


@endpoint(route_name='message_image', request_method='GET', requires_actor=True)
@endpoint(route_name='message_image_sizes', request_method='GET', requires_actor=True)
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


@endpoint(route_name='message_file_download', request_method='GET', requires_actor=True)
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


@endpoint(route_name='user_conversation_messages', request_method='POST', restricted='Manager', requires_actor=True)
@endpoint(route_name='messages', request_method='POST', requires_actor=True)
def add_message(context, request):
    """
         Adds a message to a conversation. The request.actor is the one "talking", either
         if it was the authenticaded user, the rest username or the post body actor, in this order.
    """
    cid = request.matchdict['id']
    message_params = {'actor': request.actor,
                      'verb': 'post',
                      'contexts': [{'objectType': 'conversation',
                                    'id': cid
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

