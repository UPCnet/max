import json
from bson import json_util
from datetime import datetime
from rfc3339 import rfc3339


from pymongo.objectid import ObjectId


def decodeBSONEntity(di, key):
    """
        Inspired by pymongo bson.json_util.default, but specially processing some value types:

        ObjectId --> hexvalue
        datetime --> rfc3339

        Also, while json_util.default creates a new dict in the form {$name: decodedvalue} we assign
        the decoded value, 'flattening' the value directly in the field.

        Fallback to other values using json_util.default, and flattening only those decoded entities
        that has only one key.
    """
    value = di[key]
    if isinstance(value, ObjectId):
        di[key] = str(value)
        return
    if isinstance(value, datetime):
        di[key] = rfc3339(value)
        return
    try:
        decoded = json_util.default(di[key])
        if len(decoded.keys()) == 1:
            di[key] = decoded[decoded.keys()[0]]
        else:
            di[key] = decoded
    except:
        pass


def deUnderescore(di, key):
    """
        Renames a dict key, removing underscores from the begginning of the key
    """
    if key.startswith('_'):
        di[key.lstrip('_')] = di[key]
        del di[key]


def flattendict(di):
    """
        Flattens key/values of a dict and continues the recursion
    """
    for key in di.keys():
        value = di[key]
        if isinstance(value, dict) or isinstance(value, list):
            flatten(value)
        else:
            decodeBSONEntity(di, key)
            deUnderescore(di, key)


def flatten(data):
    """
        Recursively flatten a dict or list
    """
    if isinstance(data, list):
        for item in data:
            flatten(item)
    if isinstance(data, dict):
        flattendict(data)


def checkRequestConsistency(request):
    if request.content_type != 'application/json':
        raise

    # TODO: Do more consistency checks


def extractPostData(request):
    if request.body:
        return json.loads(request.body, object_hook=json_util.object_hook)
    else:
        return {}

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


def checkDataAddUser(data):
    if not 'displayName' in data:
        raise


def checkIsValidUser(context, data):
    """Searches a user by displayName in the db and returns its id if found.
       Do additional check about the content of the data (eg: 'author' is a valid system username) """

    username = data['actor']['displayName']
    #userid = ObjectId(data['actor']['id'])

    result = context.db.users.find_one({'displayName': username}, {'displayName': 1})
    if result:
        data['actor']['id'] = result.get('_id')
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
    #followerid = ObjectId(data['actor']['id'])

    following = data['object']['displayName']
    #followingid = ObjectId(data['object']['id'])

    # Same user, can't follow yourself, abort
    if follower == following:
        raise

    result_follower = context.db.users.find_one({'displayName': follower}, {'displayName': 1})
    result_following = context.db.users.find_one({'displayName': following}, {'displayName': 1})

    if result_follower and result_following:
        data['actor']['id'] = result_follower.get('_id')
        data['object']['id'] = result_following.get('_id')
        return True
    else:
        raise
#    if result_follower.get('displayName') == follower and result_following.get('displayName') == following:
#        return True
#    else:
#        raise
