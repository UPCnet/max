import json
from bson import json_util

from pymongo.objectid import ObjectId


def checkRequestConsistency(request):
    if request.content_type != 'application/json':
        raise

    # TODO: Do more consistency checks


def extractPostData(request):
    return json.loads(request.body, object_hook=json_util.object_hook)

    # TODO: Do more syntax and format checks of sent data


def checkDataActivity(data):
    if not 'actor' in data:
        raise
    if not 'verb' in data:
        raise
    if not data['verb'] == 'post':
        raise

    # TODO: Check if data sent is consistent with JSON activitystrea.ms standard specs


def checkDataComment(data):
    if not 'actor' in data:
        raise

    # TODO: Check if data sent is consistent with JSON activitystrea.ms standard specs


def checkDataFollow(data):
    if not 'actor' in data:
        raise
    if not 'verb' in data:
        raise
    if not data['verb'] == 'follow':
        raise

    # TODO: Check if data sent is consistent with JSON activitystrea.ms standard specs


def checkIsValidUser(context, data):
    """ Do additional check about the content of the data (eg: 'author' is a valid system username) """

    username = data['actor']['displayName']
    userid = ObjectId(data['actor']['id'])

    result = context.db.users.find_one({'_id': userid}, {'displayName': 1})

    if result.get('displayName') == username:
        return True
    else:
        raise

    # Determine if it's necessary do additional checks against the request data
