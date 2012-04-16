# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented

from max.decorators import MaxRequest, MaxResponse
from max.MADMax import MADMaxCollection
from max.models import Activity
from max.rest.ResourceHandlers import JSONResourceEntity
from max.oauth2 import oauth2


@view_config(route_name='subscriptions', request_method='GET')
def getUserSubscriptions(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='subscriptions', request_method='POST', permission='operations')
@MaxResponse
@MaxRequest
def subscribe(context, request):
    """
        /people/{username}/subscriptions
    """
    # XXX For now only one context can be subscribed at a time
    actor = request.actor
    rest_params = {'actor': actor,
                   'verb': 'subscribe'}

    # Initialize a Activity object from the request
    newactivity = Activity()
    newactivity.fromRequest(request, rest_params=rest_params)

    code = 201
    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    contexts = MADMaxCollection(context.db.contexts, query_key='url')
    scontext = contexts[newactivity['object']['url']]
    actor.addSubscription(scontext)

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='subscriptions', request_method='DELETE')
def unsubscribe(context, request):
    """
    """
    return HTTPNotImplemented()


###################### Per comprovar els follows/unfollows al afegir, cal comprovar que no el segueixi previament


# @view_config(context=Root, request_method='POST', name="follow_context")
# def followContext(context, request):
#     # import ipdb; ipdb.set_trace()
#     try:
#         checkRequestConsistency(request)
#         data = extractPostData(request)
#     except:
#         return HTTPBadRequest()

#     try:
#         checkDataFollowContext(data)
#         checkIsValidUser(context, data)
#     except:
#         return HTTPBadRequest()

#     # Check if already follows

#     # Once verified the id of the users, convert their userid to an ObjectId
#     data['actor']['_id'] = ObjectId(data['actor']['id'])
#     del data['actor']['id']

#     # Set published date format
#     published = rfc3339(time.time())
#     data['published'] = published

#     # Insert activity in the database
#     context.db.activity.insert(data)

#     context.db.users.update({'_id': data['actor']['_id']},
#                             {'$push': {'subscribedTo.items': {'url': data['object']['url']}},
#                             '$inc': {'subscribedTo.totalItems': 1}})

#     return HTTPOk()


# @view_config(context=Root, request_method='POST', name="unfollow_context")
# def unFollowContext(context, request):
#     # import ipdb; ipdb.set_trace()
#     try:
#         checkRequestConsistency(request)
#         data = extractPostData(request)
#     except:
#         return HTTPBadRequest()

#     try:
#         checkDataunFollowContext(data)
#         checkIsValidUser(context, data)
#     except:
#         return HTTPBadRequest()

#     # Check if already not follows

#     # Once verified the id of the users, convert their userid to an ObjectId
#     data['actor']['_id'] = ObjectId(data['actor']['id'])
#     del data['actor']['id']

#     # Set published date format
#     published = rfc3339(time.time())
#     data['published'] = published

#     # Insert activity in the database
#     context.db.activity.insert(data)

#     context.db.users.update({'_id': data['actor']['_id']},
#                             {'$pull': {'subscribedTo.items': {'url': data['object']['url']}},
#                             '$inc': {'subscribedTo.totalItems': -1}})

#     return HTTPOk()
