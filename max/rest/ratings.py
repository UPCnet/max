from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk

import json
from bson import json_util
from pymongo.objectid import ObjectId

from max.resources import Root
from max.rest.utils import checkIsValidActivity, checkDataLike, checkIsValidUser, checkRequestConsistency, extractPostData

import time
from rfc3339 import rfc3339
from copy import deepcopy


@view_config(context=Root, request_method='POST', name="like")
def Like(context, request):
    try:
        checkRequestConsistency(request)
        data = extractPostData(request)
    except:
        return HTTPBadRequest()

    try:
        checkDataLike(data)
        checkIsValidUser(context, data)
        checkIsValidActivity(context, data)
    except:
        return HTTPBadRequest()

    # Once verified the id of the user, convert the userid to an ObjectId
    data['actor']['_id'] = ObjectId(data['actor']['id'])
    del data['actor']['id']

    # Once verified the activity is valid, convert the id to an ObjectId
    data['object']['_id'] = ObjectId(data['object']['id'])
    del data['object']['id']

    # Set published date format
    published = rfc3339(time.time())
    data['published'] = published

    # Insert activity in the database
    context.db.activity.insert(data)

    # Search for the referenced activity by id and update his likes.items field
    person = {'_id': data['actor']['_id'], 'objectType': 'person', 'username': data['actor']['username']}

    context.db.activity.update({'_id': data['object']['_id']},
                               {
                                    '$push': {'object.likes.items': person},
                                    '$inc': {'object.likes.totalItems': 1}
                               })

    return HTTPOk()
