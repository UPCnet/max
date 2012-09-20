# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented

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


@view_config(route_name='conversation', request_method='POST')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def postMessage2Conversation(context, request):
    """
         /conversations/{chash}
         Post message to a conversation
    """
    conversation_params = dict(chash=request.matchdict['chash'],
                               actor=request.actor)

    # Initialize a conversation (context) object from the request
    newconversation = Context()
    newconversation.fromRequest(request, rest_params=conversation_params)

    if not newconversation.get('_id'):
        # New conversation
        contextid = newconversation.insert()
        newconversation['_id'] = contextid

    message_params = {'actor': request.actor,
                      'verb': 'post'}

    # Initialize a Message (Activity) object from the request
    newmessage = Activity()
    newmessage.fromRequest(request, rest_params=message_params)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newmessage.get('_id'):
        # Already Exists
        code = 200
    else:
        # New conversation
        code = 201
        message_oid = newmessage.insert()
        newmessage['_id'] = message_oid

    handler = JSONResourceEntity(newmessage.flatten(), status_code=code)
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
