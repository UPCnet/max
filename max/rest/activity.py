from pyramid.view import view_config

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk

import json
from bson import json_util
from pymongo.objectid import ObjectId

from max.resources import Root
from max.models import Activity
from max.rest.utils import checkIsValidRepliedActivity, checkIsValidUser, checkDataActivity, checkDataComment, checkRequestConsistency, extractPostData

import time
from rfc3339 import rfc3339


@view_config(context=Root, request_method='POST', name="activity")
def addActivity(context, request):
    try:
        checkRequestConsistency(request)
        data = extractPostData(request)
    except:
        return HTTPBadRequest()

    try:
        checkDataActivity(data)
        checkIsValidUser(context, data)
    except:
        return HTTPBadRequest()

    newactivity = Activity({'actor': {
                                'objectType': 'person',
                                '_id': ObjectId(data['actor']['id']),
                                'displayName': data['actor']['displayName']
                                },
                            'verb': 'post',
                            'object': {
                                'objectType': 'note',
                                'content': data['object']['content']
                                }
                            })

    # # Once verified the id of the user, convert the userid to an ObjectId
    # data['actor']['_id'] = ObjectId(data['actor']['id'])
    # del data['actor']['id']

    # # Set published date format
    # published = rfc3339(time.time())
    # data['published'] = published

    # Insert activity in the database
    context.db[newactivity.collection].insert(newactivity)
    return HTTPOk()


@view_config(context=Root, request_method='POST', name="comment")
def addComment(context, request):
    try:
        checkRequestConsistency(request)
        data = extractPostData(request)
    except:
        return HTTPBadRequest()

    try:
        checkDataComment(data)
        checkIsValidUser(context, data)
        checkIsValidRepliedActivity(context, data)
    except:
        return HTTPBadRequest()

    newactivity = Activity({'actor': {
                                'objectType': 'person',
                                '_id': ObjectId(data['actor']['id']),
                                'displayName': data['actor']['displayName']
                                },
                            'verb': 'post',
                            'object': {
                                'objectType': 'comment',
                                'content': data['object']['content'],
                                'inReplyTo': [
                                              {
                                                "_id": ObjectId(data['object']['inReplyTo'][0]['id']),
                                              }
                                            ]
                                }
                            })

    # Once verified the id of the user, convert the userid to an ObjectId
    # data['actor']['_id'] = ObjectId(data['actor']['id'])
    # del data['actor']['id']

    # Once verified the activity is valid, convert the id to an ObjectId
    activityid = ObjectId(data['object']['inReplyTo'][0]['id'])
    del data['object']['inReplyTo']
    data['object']['inReplyTo'] = []
    data['object']['inReplyTo'].append({'_id': activityid})

    # Set published date format
    # published = rfc3339(time.time())
    # data['published'] = published

    # Insert activity in the database
    context.db.activity.insert(data)

    # Search for the referenced activity by id and update his replies.items field
    comment = {
        "_id": data['_id'],
        "objectType": "comment",
        "author": {
            "id": data['actor']['_id'],
            "displayName": data['actor']['displayName']
        },
        "content": data['object']['content'],
    }

    # import ipdb; ipdb.set_trace( )
    context.db.activity.update(data['object']['inReplyTo'][0],
                                {
                                    '$push': {'object.replies.items': comment},
                                    '$inc': {'object.replies.totalItems': 1}
                                })

    return HTTPOk()
