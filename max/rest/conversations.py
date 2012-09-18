from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented

from max.MADMax import MADMaxDB
from max.models import Activity
from max.decorators import MaxRequest, MaxResponse
from max.oauth2 import oauth2
from max.exceptions import MissingField, Unauthorized

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
def postConversation(context, request):
    """
         /conversation/{hash}
         Post message to a conversation
    """
    rest_params = {'actor': request.actor,
                   'verb': 'post'}

    # Initialize a Activity object from the request
    newactivity = Activity()
    newactivity.fromRequest(request, rest_params=rest_params)


@view_config(route_name='messages', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getMessages(context, request):
    """
         /conversations/{hash}/messages
         Return all messages from a conversation
    """
