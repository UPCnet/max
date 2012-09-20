# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented

from max.exceptions import ValidationError
from max.MADMax import MADMaxDB
from max.models import Activity, Context
from max.decorators import MaxRequest, MaxResponse
from max.oauth2 import oauth2

from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.rest.utils import searchParams, canReadContext
import re


@view_config(route_name='conversations', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getConversations(context, request):
    """
         /conversations
         Return all conversations depending on the actor requester
    """
    mmdb = MADMaxDB(context.db)
    query = {'object.participants': {'$in': request.actor['username']},
             'object.objectType': 'Conversation',
             }

    conversations = mmdb.contexts.search(query, sort="published", flatten=1)

    handler = JSONResourceRoot(conversations)
    return handler.buildResponse()


@view_config(route_name='conversations', request_method='POST')
# @MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def postMessage2Conversation(context, request):
    """
         /conversations
         Post message to a conversation
    """
    conversation_params = dict(actor=request.actor)

    # Initialize a conversation (context) object from the request
    newconversation = Context()
    newconversation.fromRequest(request, rest_params=conversation_params)

    if not request.actor.username in newconversation.object['participants']:
        raise ValidationError('Actor must be part of the participants list.')

    if not newconversation.get('_id'):
        # New conversation
        contextid = newconversation.insert()
        newconversation['_id'] = contextid

    # Subscriure user
    request.actor.addSubscription(newconversation)

    message_params = {'actor': request.actor,
                      'verb': 'post'}

    # Initialize a Message (Activity) object from the request
    newmessage = Activity()
    newmessage.fromRequest(request, rest_params=message_params)

    message_oid = newmessage.insert()
    newmessage['_id'] = message_oid

    handler = JSONResourceEntity(newmessage.flatten(), status_code=201)
    return handler.buildResponse()


@view_config(route_name='messages', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getMessages(context, request):
    """
         /conversations/{hash}/messages
         Return all messages from a conversation
    """
