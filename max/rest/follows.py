from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError, HTTPNotImplemented
from max.exceptions import MissingField
from max.MADMax import MADMaxDB, MADMaxCollection
from max.models import User
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity

from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError

from max.MADMax import MADMaxDB
from max.models import Activity
from max.exceptions import MissingField

from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity


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
def follow(context, request):
    """
    """
    return HTTPNotImplemented()

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
