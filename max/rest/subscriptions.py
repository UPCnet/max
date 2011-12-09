from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk

import json
from bson import json_util
from pymongo.objectid import ObjectId
from max.resources import Root
from max.rest.utils import checkDataunFollowContext, checkDataFollowContext, checkIsValidUser, checkAreValidFollowUsers, checkDataFollow, checkDataunFollow, checkRequestConsistency, extractPostData

import time
from rfc3339 import rfc3339
from copy import deepcopy


@view_config(context=Root, request_method='POST', name="follow")
def Follow(context, request):
    # import ipdb; ipdb.set_trace()
    try:
        checkRequestConsistency(request)
        data = extractPostData(request)
    except:
        return HTTPBadRequest()

    try:
        checkDataFollow(data)
        checkAreValidFollowUsers(context, data)
    except:
        return HTTPBadRequest()

    # Check if already follows

    # Once verified the id of the users, convert their userid to an ObjectId
    data['actor']['_id'] = ObjectId(data['actor']['id'])
    del data['actor']['id']

    data['object']['_id'] = ObjectId(data['object']['id'])
    del data['object']['id']

    # Set published date format
    published = rfc3339(time.time())
    data['published'] = published

    # Insert activity in the database
    context.db.activity.insert(data)

    context.db.users.update({'_id': data['actor']['_id']},
                            {
                                '$push': {'following.items': {'_id': data['object']['_id']}},
                                '$inc': {'following.totalItems': 1}
                            })

    return HTTPOk()


@view_config(context=Root, request_method='POST', name="unfollow")
def unFollow(context, request):
    # import ipdb; ipdb.set_trace()
    try:
        checkRequestConsistency(request)
        data = extractPostData(request)
    except:
        return HTTPBadRequest()

    try:
        checkDataunFollow(data)
        checkAreValidFollowUsers(context, data)
    except:
        return HTTPBadRequest()

    # Check if already follows

    # Once verified the id of the users, convert their userid to an ObjectId
    data['actor']['_id'] = ObjectId(data['actor']['id'])
    del data['actor']['id']

    data['object']['_id'] = ObjectId(data['object']['id'])
    del data['object']['id']

    # Set published date format
    published = rfc3339(time.time())
    data['published'] = published

    # Insert activity in the database
    context.db.activity.insert(data)

    context.db.users.update({'_id': data['actor']['_id']},
                            {
                                '$pull': {'following.items': {'_id': data['object']['_id']}},
                                '$inc': {'following.totalItems': -1}
                            })

    return HTTPOk()


@view_config(context=Root, request_method='POST', name="follow_context")
def followContext(context, request):
    # import ipdb; ipdb.set_trace()
    try:
        checkRequestConsistency(request)
        data = extractPostData(request)
    except:
        return HTTPBadRequest()

    try:
        checkDataFollowContext(data)
        checkIsValidUser(context, data)
    except:
        return HTTPBadRequest()

    # Check if already follows

    # Once verified the id of the users, convert their userid to an ObjectId
    data['actor']['_id'] = ObjectId(data['actor']['id'])
    del data['actor']['id']

    # Set published date format
    published = rfc3339(time.time())
    data['published'] = published

    # Insert activity in the database
    context.db.activity.insert(data)

    context.db.users.update({'_id': data['actor']['_id']},
                            {'$push': {'subscribedTo.items': {'url': data['object']['url']}},
                            '$inc': {'subscribedTo.totalItems': 1}})

    return HTTPOk()


@view_config(context=Root, request_method='POST', name="unfollow_context")
def unFollowContext(context, request):
    # import ipdb; ipdb.set_trace()
    try:
        checkRequestConsistency(request)
        data = extractPostData(request)
    except:
        return HTTPBadRequest()

    try:
        checkDataunFollowContext(data)
        checkIsValidUser(context, data)
    except:
        return HTTPBadRequest()

    # Check if already not follows

    # Once verified the id of the users, convert their userid to an ObjectId
    data['actor']['_id'] = ObjectId(data['actor']['id'])
    del data['actor']['id']

    # Set published date format
    published = rfc3339(time.time())
    data['published'] = published

    # Insert activity in the database
    context.db.activity.insert(data)

    context.db.users.update({'_id': data['actor']['_id']},
                            {'$pull': {'subscribedTo.items': {'url': data['object']['url']}},
                            '$inc': {'subscribedTo.totalItems': -1}})

    return HTTPOk()
