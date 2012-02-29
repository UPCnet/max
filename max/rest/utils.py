import json
from bson import json_util
from datetime import datetime
from rfc3339 import rfc3339
from max.exceptions import InvalidSearchParams

from pymongo.objectid import ObjectId

import requests
import urllib2
import re


def searchParams(request):
    """
        Extracts valid search params from the request, or sets default values if not found
        Returns a dict with all the results
        Raises InvalidSearchParams on bad param values
    """
    params = {}
    limit = request.params.get('limit', 10)
    try:
        params['limit'] = int(limit)
    except:
        raise InvalidSearchParams, 'limit must be a positive integer'

    since = request.params.get('since')
    if since:
        try:
            params['since'] = ObjectId(since)
        except:
            raise InvalidSearchParams, 'since must be a valid ObjectId BSON identifier'


    return params


class RUDict(dict):

    def __init__(self, *args, **kw):
        super(RUDict, self).__init__(*args, **kw)

    def update(self, E=None, **F):
        if E is not None:
            if 'keys' in dir(E) and callable(getattr(E, 'keys')):
                for k in E:
                    if k in self:  # existing ...must recurse into both sides
                        self.r_update(k, E)
                    else:  # doesn't currently exist, just update
                        self[k] = E[k]
            else:
                for (k, v) in E:
                    self.r_update(k, {k: v})

        for k in F:
            self.r_update(k, {k: F[k]})

    def r_update(self, key, other_dict):
        if isinstance(self[key], dict) and isinstance(other_dict[key], dict):
            od = RUDict(self[key])
            nd = other_dict[key]
            od.update(nd)
            self[key] = od
        else:
            self[key] = other_dict[key]


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
        di[key] = rfc3339(value, utc=True, use_system_timezone=False)
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


def formatMessageEntities(text):
    """
        function that shearches for elements in the text that have to be formatted.
        Currently shortens urls.
        XXX TODO find @usernames to acces profiles
    """
    def shorten(matchobj):
        return shortenURL(matchobj.group(0))

    find_url_regex = r'((https?\:\/\/)|(www\.))(\S+)(\w{2,4})(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?'
    shortened = re.sub(find_url_regex, shorten, text)

    return shortened


def shortenURL(url):
    """
        Shortens a url using bitly API. Keeps the original url in case
        something goes wrong with the api call
    """
    # FOR DEBUGGING !! if localhost present in the domain part of the url,
    # substitute with a fake domain
    # to allow bitly shortening in development environments
    # (localhost/ port not allowed in URI by bitly api)
    url = re.sub(r'(.*://)(localhost:[0-9]{4,5})(.*)', r'\1foo.bar\3', url)

    bitly_username = 'maxclient'
    bitly_api_key = 'R_33a0cbaa2d41c3957dc5a40a0b2c2760'

    params = {'api_url': 'http://api.bitly.com',
              'login': 'apiKey=%s&login=%s' % (bitly_api_key, bitly_username),
              'version': 'v3',
              'endpoint': 'shorten',
              'endpoint_params': 'longUrl=%s' % (urllib2.quote(url))
             }

    queryurl = '%(api_url)s/%(version)s/%(endpoint)s?%(login)s&%(endpoint_params)s' % params

    req = requests.get(queryurl)

    try:
        response = json.loads(req.content)
        if response.get('status_code', None) == 200:
            if 'data' in response.keys():
                return response['data']['url']
    except:
        return url
    return url

def checkRequestConsistency(request):
    if request.content_type != 'application/json':
        raise

    # TODO: Do more consistency checks


def extractPostData(request):
    if request.body:
        json_data = json.loads(request.body, object_hook=json_util.object_hook)
    else:
        json_data = {}

    return json_data
    # TODO: Do more syntax and format checks of sent data


def checkQuery(data):
    if not 'username' in data and not 'context' in data:
        raise


def checkIsValidQueryUser(context, data):
    username = data['username']

    result = context.db.users.find_one({'username': username})

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
    if not 'username' in data:
        raise


def checkIsValidUser(context, data):
    """Searches a user by username in the db and returns its id if found.
       Do additional check about the content of the data (eg: 'author' is a valid system username) """

    username = data['actor']['username']
    #userid = ObjectId(data['actor']['id'])

    result = context.db.users.find_one({'username': username}, {'username': 1})
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
    follower = data['actor']['username']
    #followerid = ObjectId(data['actor']['id'])

    following = data['object']['username']
    #followingid = ObjectId(data['object']['id'])

    # Same user, can't follow yourself, abort
    if follower == following:
        raise

    result_follower = context.db.users.find_one({'username': follower}, {'username': 1})
    result_following = context.db.users.find_one({'username': following}, {'username': 1})

    if result_follower and result_following:
        data['actor']['id'] = result_follower.get('_id')
        data['object']['id'] = result_following.get('_id')
        return True
    else:
        raise
#    if result_follower.get('username') == follower and result_following.get('username') == following:
#        return True
#    else:
#        raise
