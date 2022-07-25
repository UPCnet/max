# -*- coding: utf-8 -*-
from max.MADMax import MADMaxCollection
from max.models import Message
from max.rabbitmq import RabbitNotifications
from max.rest import JSONResourceEntity
from max.rest import JSONResourceRoot
from max.rest import endpoint
from max.security.permissions import add_message
from max.security.permissions import list_messages
from max.security.permissions import view_message
from max.utils import searchParams
from max.utils.dicts import flatten

from pyramid.httpexceptions import HTTPGone
from pyramid.response import Response

from base64 import b64encode
from bson import ObjectId
from pymongo import DESCENDING


@endpoint(route_name='messages', request_method='GET', permission=list_messages)
def getMessages(message, request):
    """
        Get all messages
    """
    is_head = request.method == 'HEAD'
    activities = request.db.messages.search({'verb': 'post'}, flatten=1, count=is_head, **searchParams(request))
    handler = JSONResourceRoot(request, activities, stats=is_head)
    return handler.buildResponse()


@endpoint(route_name='conversation_messages', request_method='GET', permission=list_messages)
def getConversationMessages(conversation, request):
    """
        Get all messages from a conversation
    """
    query = {'contexts.id': str(conversation['_id'])}

    # Sorting by _id, as id is indeed the same as published
    messages = request.db.messages.search(query, sort_direction=DESCENDING, sort_by_field="_id", keep_private_fields=False, **searchParams(request))
    inverted = flatten(messages, reverse=True)
    handler = JSONResourceRoot(request, inverted, remaining=messages.remaining)
    return handler.buildResponse()


@endpoint(route_name='user_conversation_messages', request_method='POST', permission=add_message)
@endpoint(route_name='conversation_messages', request_method='POST', permission=add_message)
def add_message(conversation, request):
    """
        Adds a message to a conversation

        The request.actor is the one "talking", either if it was the authenticated user,
        the rest username or the post body actor, in this order.
    """

    try:
        mobile = request.decoded_payload['object']['mobile']
    except:
        mobile = False

    message_params = {'actor': request.actor,
                      'verb': 'post',
                      'contexts': [conversation]
                      }

    if 'single' in message_params['contexts'][0]['tags']:
        users = MADMaxCollection(request, 'users', query_key='username')
        for participant in message_params['contexts'][0]['participants']:
            user = users[participant['username']]
            if user.getSubscription(conversation) is None:
                user.addSubscription(conversation)
                conversation['tags'].remove('single')
                conversation.save()
                notifier = RabbitNotifications(request)
                notifier.add_conversation(conversation)


    # Initialize a Message (Activity) object from the request
    newmessage = Message.from_request(request, rest_params=message_params)

    if newmessage['object']['objectType'] == u'image' or \
       newmessage['object']['objectType'] == u'file':
        # Extract the file before saving object
        message_file = newmessage.extract_file_from_activity()
        message_oid = newmessage.insert()
        newmessage['_id'] = ObjectId(message_oid)
        newmessage.process_file(request, message_file)
        newmessage.save()
        if mobile:
            notifier = RabbitNotifications(request)
            notifier.add_conversation_message(conversation, newmessage)
    else:
        message_oid = newmessage.insert()
        newmessage['_id'] = message_oid
        if mobile:
            notifier = RabbitNotifications(request)
            notifier.add_conversation_message(conversation, newmessage)

    handler = JSONResourceEntity(request, newmessage.flatten(), status_code=201)
    return handler.buildResponse()


@endpoint(route_name='message_image', request_method='GET', permission=view_message)
@endpoint(route_name='message_image_sizes', request_method='GET', permission=view_message)
def getMessageImageAttachment(message, request):
    """
        Get a message image
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


@endpoint(route_name='message_file_download', request_method='GET', permission=view_message)
def getMessageFileAttachment(message, request):
    """
        Get a message file
    """
    file_data, mimetype = message.getFile()

    if file_data is not None:
        from_app = request.headers.get('X-From', 'None') # app or None
        if from_app == 'App':
            pdf = b64encode(file_data)
            mimetype = 'application/base64'
            response = Response(pdf, status_int=200)
        else:
            response = Response(file_data, status_int=200)
        response.content_type = mimetype
        filename = message['object'].get('filename', message['_id'])
        response.headers.add('Content-Disposition', 'attachment; filename={}'.format(filename))
    else:
        response = HTTPGone()

    return response
