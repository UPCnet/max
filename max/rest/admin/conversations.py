# -*- coding: utf-8 -*-
from pyramid.view import view_config
from max.rest.utils import searchParams

from max.MADMax import MADMaxDB, MADMaxCollection
from max.decorators import MaxResponse, requirePersonActor
from max.oauth2 import oauth2
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.models import Message
from bson import ObjectId


@view_config(route_name='pushtokens', request_method='GET', restricted='Manager')
@MaxResponse
@oauth2(['widgetcli'])
def getPushTokensForConversation(context, request):
    """
         /conversations/{id}/tokens
         Return all relevant tokens for a given conversation
    """

    cid = request.matchdict['id']
    conversations = MADMaxCollection(context.db.conversations)
    conversation = conversations[cid]

    mmdb = MADMaxDB(context.db)
    query = {"username": {"$in": [user['username'] for user in conversation['participants']]}}
    users = mmdb.users.search(query, show_fields=["username", "iosDevices", "androidDevices"], sort="username", flatten=1, **searchParams(request))

    result = []
    for user in users:
        for idevice in user.get('iosDevices', []):
            result.append(dict(token=idevice, platform='iOS', username=user.get('username')))
        for adevice in user.get('androidDevices', []):
            result.append(dict(token=adevice, platform='android', username=user.get('username')))

    handler = JSONResourceRoot(result)
    return handler.buildResponse()


@view_config(route_name='user_conversation_messages', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor(force_own=False, exists=True)
def addMessage(context, request):
    """
         /people/{username}/conversations/{id}/messages
         Post a message to 1 (one) existing conversation
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
