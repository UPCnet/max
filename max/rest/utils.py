# -*- coding: utf-8 -*-
import json
from bson import json_util
from datetime import datetime
from rfc3339 import rfc3339
from max.exceptions import InvalidSearchParams, Unauthorized

from bson.objectid import ObjectId
from max.MADMax import MADMaxCollection

import requests
import logging
import urllib2
import re
import sys

UNICODE_ACCEPTED_CHARS = u'áéíóúàèìòùïöüçñ'

FIND_URL_REGEX = r'((https?\:\/\/)|(www\.))(\S+)(\w{2,4})(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?'
FIND_HASHTAGS_REGEX = r'(\s|^)#{1}([\w\-\_\.%s]+)' % UNICODE_ACCEPTED_CHARS
FIND_KEYWORDS_REGEX = r'(\s|^)[#\'\"]?([\w\-\_\.%s]{3,})[\"\']?' % UNICODE_ACCEPTED_CHARS


def getMaxModelByObjectType(objectType):
    return getattr(sys.modules['max.models'], objectType.capitalize(), None)


def downloadTwitterUserImage(twitterUsername, filename):
    """
    """
    try:
        req = requests.get('http://api.twitter.com/1/users/show.json?screen_name=%s' % twitterUsername)
        data = json.loads(req.text)
        image_url = data.get('profile_image_url_https', None)
        if image_url:
            req = requests.get(image_url)
            open(filename, 'w').write(req.content)
            return True
        else:
            logger = logging.getLogger('max')
            logger.error("An error occurred while downloading twitter user image!")
    except:
        logger = logging.getLogger('max')
        logger.error("An error occurred while downloading twitter user image!")
        return False


def getUserIdFromTwitter(twitterUsername):
    res = requests.get('http://api.twitter.com/1/users/show.json?screen_name=%s' % twitterUsername)

    if res.status_code == 404:
        return None

    return json.loads(res.text).get('id_str', None)


def getUsernameFromXOAuth(request):
    """
    """
    return request.headers.get('X-Oauth-Username')


def getUsernameFromURI(request):
    """
    """
    return request.matchdict.get('username', None)


def getUrlHashFromURI(request):
    """
    """
    return request.matchdict.get('hash', None)


def getUsernameFromPOSTBody(request):
    """
    """
    return extractPostData(request).get('actor', {}).get('username', None)


def isOauth(request):
    """
    """
    keys = request.headers.keys()
    return 'X-Oauth-Username' in keys and 'X-Oauth-Token' in keys and 'X-Oauth-Scope' in keys


def isBasic(request):
    """
    """
    if request.authorization:
        return request.authorization[0].lower() == 'basic'
    else:
        return False


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
        raise InvalidSearchParams('limit must be a positive integer')

    after = request.params.get('after')
    if after:
        try:
            params['after'] = ObjectId(after)
        except:
            raise InvalidSearchParams('after must be a valid ObjectId BSON identifier')

    before = request.params.get('before')
    if before:
        try:
            params['before'] = ObjectId(before)
        except:
            raise InvalidSearchParams('before must be a valid ObjectId BSON identifier')

    if 'before' in params and 'after' in params:
        raise InvalidSearchParams('only one offset filter is allowed, after or before')

    hashtags = request.params.getall('hashtag')
    if hashtags:
        params['hashtag'] = [hasht.lower() for hasht in hashtags]

    actor = request.params.get('actor')
    if actor:
        params['actor'] = actor.lower()

    keywords = request.params.getall('keyword')
    if keywords:
        ### XXX Split or regex?
        params['keywords'] = [keyw.lower() for keyw in keywords]

    username = request.params.get('username')
    if username:
        params['username'] = username.lower()

    tags = request.params.getall('tags')
    if tags:
        retags = []
        for tag in tags:
            retag = re.sub(r'\s*(\w+)\s*', r'\1', tag, re.UNICODE)
            if retag:
                retags.append(retag)
        if retags:
            params['tags'] = retags

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


def clearPrivateFields(di):
    """
        Clears all fields starting with _ except _id
    """
    for key in di.keys():
        if key.startswith('_') and key not in ['_id']:
            del di[key]


def flattendict(di, **kwargs):
    """
        Flattens key/values of a dict and continues the recursion
    """
    di = dict(di)
    if not kwargs.get('keep_private_fields', True):
        clearPrivateFields(di)

    for key in di.keys():
        value = di[key]
        if isinstance(value, dict) or isinstance(value, list):
            di[key] = flatten(value, **kwargs)
        else:
            decodeBSONEntity(di, key)
        deUnderescore(di, key)
    return di


def flatten(data, **kwargs):
    """
        Recursively flatten a dict or list
    """
    if isinstance(data, list):
        newitems = []
        for item in data:
            newitems.append(flatten(item, **kwargs))
        data = newitems
    if isinstance(data, dict):
        data = flattendict(data, **kwargs)
    return data


def formatMessageEntities(text):
    """
        function that shearches for elements in the text that have to be formatted.
        Currently shortens urls.
    """
    def shorten(matchobj):
        return shortenURL(matchobj.group(0))

    shortened = re.sub(FIND_URL_REGEX, shorten, text)

    return shortened


def findHashtags(text):
    """
        Returns a list of valid #hastags in text
        Narrative description of the search pattern will be something like:
        "Any group of alphanumeric characters preceded by one (and only one) hash (#)
         At the begginning of a string or before a whitespace"

        teststring = "#first # Hello i'm a #text with #hashtags but#some are not valid#  # ##double #last"
        should return ['first', 'text', 'hashtags', 'last']
    """
    hashtags = [a.groups()[1] for a in re.finditer(FIND_HASHTAGS_REGEX, text)]
    lowercase = [hasht.lower() for hasht in hashtags]
    return lowercase


def findKeywords(text):
    """
        Returns a list of valid keywords, including hashtags (without the hash),
        excluding urls and words shorter than the defined in KEYWORD_MIN_LENGTH.
        Keywords are stored in lowercase.
    """
    _text = text.lower()
    stripped_urls = re.sub(FIND_URL_REGEX, '', _text)
    keywords = [kw.groups()[1] for kw in re.finditer(FIND_KEYWORDS_REGEX, stripped_urls)]
    return keywords


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


def extractPostData(request):
    if request.body:
        json_data = json.loads(request.body, object_hook=json_util.object_hook)
    else:
        json_data = {}

    return json_data
    # TODO: Do more syntax and format checks of sent data


def canWriteInContexts(actor, contexts):
    """
    """
    # If no context filter defined, write/read is always allowed
    if contexts == []:
        return True

    subscriptions = {}

    for context in contexts:
        subscription = subscriptions.get(context.getIdentifier(), None)
        if subscription is None:
            #update subscriptions dict
            u_field = context.unique.lstrip('_')
            subsc = dict([(a[u_field], a) for a in actor.get(context.user_subscription_storage, {}).get('items', [])])
            subscriptions.update(subsc)
            subscription = subscriptions.get(context.getIdentifier(), None)
            if subscription is None:
                raise Unauthorized("You are not subscribed to this context : %s" % context.getIdentifier())

        # If user is trying to post on a subscribed context/s
        # Check that has write permission in all the contexts

        allowed_to_write = 'write' in subscription.get('permissions', [])
        if not allowed_to_write:
            raise Unauthorized("You are not allowed to post to this context : %s" % context.getIdentifier())

    # If we reached here, we have permission to post on all contexts
    return True


def canReadContext(actor, url):
    """
    """
    # If no context filter defined, write/read is always allowed
    if url == []:
        return True

    subscribed_contexts_urls = [a['object']['url'] for a in actor['subscribedTo']['items'] if 'read' in a['permissions']]

    if url not in subscribed_contexts_urls:

        # Check recursive read: User is allowed to read recursively on an
        # unsubscribed context if is subscribed to at least one child context
        containments = [usc.startswith(url) for usc in subscribed_contexts_urls]
        if True not in containments:
            raise Unauthorized("You are not subscribed to this context: %s" % url)

    #If we reached here, we have permission to read on all contexts
    return True

# Old methods


def checkRequestConsistency(request):
    if request.content_type != 'application/json':
        raise

    # TODO: Do more consistency checks


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
