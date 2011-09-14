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


def checkQuery(data):
    if not 'displayName' in data and not 'context' in data:
        raise


def checkIsValidQueryUser(context, data):
    username = data['displayName']

    result = context.db.users.find_one({'displayName': username})

    if result:
        return True
    else:
        raise


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
    if not 'object' in data:
        raise
    if not data['verb'] == 'follow':
        raise
    if not 'objectType' in data['object']:
        raise
    if not 'person' in data['object']['objectType']:
        raise

    # TODO: Check if data sent is consistent with JSON activitystrea.ms standard specs


def checkDataunFollow(data):
    if not 'actor' in data:
        raise
    if not 'verb' in data:
        raise
    if not 'object' in data:
        raise
    if not data['verb'] == 'unfollow':
        raise
    if not 'objectType' in data['object']:
        raise
    if not 'person' in data['object']['objectType']:
        raise

    # TODO: Check if data sent is consistent with JSON activitystrea.ms standard specs


def checkDataFollowContext(data):
    if not 'actor' in data:
        raise
    if not 'verb' in data:
        raise
    if not 'object' in data:
        raise
    if not data['verb'] == 'follow':
        raise
    if not 'objectType' in data['object']:
        raise
    if not 'service' in data['object']['objectType']:
        raise


def checkDataunFollowContext(data):
    if not 'actor' in data:
        raise
    if not 'verb' in data:
        raise
    if not 'object' in data:
        raise
    if not data['verb'] == 'unfollow':
        raise
    if not 'objectType' in data['object']:
        raise
    if not 'service' in data['object']['objectType']:
        raise


def checkDataLike(data):
    if not 'actor' in data:
        raise
    if not 'verb' in data:
        raise
    if not 'object' in data:
        raise
    if not data['verb'] == 'like':
        raise
    if not 'objectType' in data['object']:
        raise


def checkDataShare(data):
    if not 'actor' in data:
        raise
    if not 'verb' in data:
        raise
    if not 'object' in data:
        raise
    if not data['verb'] == 'share':
        raise
    if not 'objectType' in data['object']:
        raise


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


def checkIsValidActivity(context, data):
    """ Do a check to validate that the activity is a registered activity """
    activityid = ObjectId(data['object']['id'])

    result = context.db.activity.find_one({'_id': activityid})

    if result:
        return True
    else:
        raise


def checkIsValidRepliedActivity(context, data):
    """ Do a check to validate that the activity whom the comment is referring is a registered activity """
    activityid = ObjectId(data['object']['inReplyTo'][0]['id'])

    result = context.db.activity.find_one({'_id': activityid})

    if result:
        return True
    else:
        raise


def checkAreValidFollowUsers(context, data):
    """ Check if both users follower and following are valid system users """
    follower = data['actor']['displayName']
    followerid = ObjectId(data['actor']['id'])

    following = data['object']['displayName']
    followingid = ObjectId(data['object']['id'])

    # Same user, can't follow yourself, abort
    if follower == following:
        raise

    result_follower = context.db.users.find_one({'_id': followerid}, {'displayName': 1})
    result_following = context.db.users.find_one({'_id': followingid}, {'displayName': 1})

    if result_follower.get('displayName') == follower and result_following.get('displayName') == following:
        return True
    else:
        raise
