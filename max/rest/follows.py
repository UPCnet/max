# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented
from max.decorators import MaxResponse, MaxRequest

from max.models import Activity

from max.rest.ResourceHandlers import JSONResourceEntity


@view_config(route_name='follows', request_method='GET')
def getFollowedUsers(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='follow', request_method='GET')
def getFollowedUser(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='follow', request_method='POST')
@MaxResponse
@MaxRequest
def follow(context, request):
    """
        /people/{username}/follows/{followedDN}'
    """
    #XXX TODO ara nomes es tracta un sol follow
    # s'ha de iterar si es vol que el comentari sigui de N follows
    actor = request.actor
    rest_params = {'actor': request.actor}

    # Initialize a Activity object from the request
    newactivity = Activity(request, rest_params=rest_params)

    code = 201
    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    actor.addFollower(newactivity['object'])

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='follow', request_method='DELETE')
def unfollow(context, request):
    """
    """
    return HTTPNotImplemented()


# @view_config(context=Root, request_method='POST', name="follow")
# def Follow(context, request):
#     # import ipdb; ipdb.set_trace()
#     try:
#         checkRequestConsistency(request)
#         data = extractPostData(request)
#     except:
#         return HTTPBadRequest()

#     try:
#         checkDataFollow(data)
#         checkAreValidFollowUsers(context, data)
#     except:
#         return HTTPBadRequest()

#     # Check if already follows

#     # Once verified the id of the users, convert their userid to an ObjectId
#     data['actor']['_id'] = ObjectId(data['actor']['id'])
#     del data['actor']['id']

#     data['object']['_id'] = ObjectId(data['object']['id'])
#     del data['object']['id']

#     # Set published date format
#     published = rfc3339(time.time())
#     data['published'] = published

#     # Insert activity in the database
#     context.db.activity.insert(data)

#     context.db.users.update({'_id': data['actor']['_id']},
#                             {
#                                 '$push': {'following.items': {'_id': data['object']['_id']}},
#                                 '$inc': {'following.totalItems': 1}
#                             })

#     return HTTPOk()


# @view_config(context=Root, request_method='POST', name="unfollow")
# def unFollow(context, request):
#     # import ipdb; ipdb.set_trace()
#     try:
#         checkRequestConsistency(request)
#         data = extractPostData(request)
#     except:
#         return HTTPBadRequest()

#     try:
#         checkDataunFollow(data)
#         checkAreValidFollowUsers(context, data)
#     except:
#         return HTTPBadRequest()

#     # Check if already follows

#     # Once verified the id of the users, convert their userid to an ObjectId
#     data['actor']['_id'] = ObjectId(data['actor']['id'])
#     del data['actor']['id']

#     data['object']['_id'] = ObjectId(data['object']['id'])
#     del data['object']['id']

#     # Set published date format
#     published = rfc3339(time.time())
#     data['published'] = published

#     # Insert activity in the database
#     context.db.activity.insert(data)

#     context.db.users.update({'_id': data['actor']['_id']},
#                             {
#                                 '$pull': {'following.items': {'_id': data['object']['_id']}},
#                                 '$inc': {'following.totalItems': -1}
#                             })

#     return HTTPOk()
