# -*- coding: utf-8 -*-
from max.exceptions import InvalidSearchParams
from max.exceptions import Unauthorized

from pyramid.settings import asbool
from pyramid.threadlocal import get_current_registry

from bson import json_util
from bson.objectid import ObjectId
from calendar import monthrange
from datetime import datetime, time
from rfc3339 import rfc3339

import json
import logging
import re
import requests
import sys
import tweepy
import urllib2


UNICODE_ACCEPTED_CHARS = u'áéíóúàèìòùïöüçñ'

FIND_URL_REGEX = r'((https?\:\/\/)|(www\.))(\S+)(\w{2,4})(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?'
FIND_HASHTAGS_REGEX = r'(\s|^)#{1}([\w\-\_\.%s]+)' % UNICODE_ACCEPTED_CHARS
FIND_KEYWORDS_REGEX = r'(\s|^)(?:#|\'|\"|\w\')?([\w\-\_\.%s]{3,})[\"\']?' % UNICODE_ACCEPTED_CHARS

EXIF_ROTATIONS = {
    3: 180,
    6: -90,
    8: -270
}


def getMaxModelByObjectType(objectType):
    return getattr(sys.modules['max.models'], objectType.capitalize(), None)


def get_twitter_api():
    registry = get_current_registry()
    twitter_settings = registry.cloudapis_settings.get('twitter', None)

    if twitter_settings:
        try:
            # Twitter auth
            auth = tweepy.OAuthHandler(twitter_settings.get('consumer_key', ''), twitter_settings.get('consumer_secret', ''))
            auth.set_access_token(twitter_settings.get('access_token', ''), twitter_settings.get('access_token_secret', ''))
            api = tweepy.API(auth)
            api.verify_credentials()
            return api
        except:
            # Some error occurred
            return None


def downloadTwitterUserImage(twitterUsername, filename):
    """
    """
    exit_status = False
    api = get_twitter_api()
    if api:
        user = api.get_user(twitterUsername)
        image_url = user.profile_image_url_https

        if image_url:
            req = requests.get(image_url, verify=False)
            if req.status_code == 200:
                open(filename, 'w').write(req.content)
                exit_status = True

    if not exit_status:
        logger = logging.getLogger('max')
        logger.error("An error occurred while downloading twitter user image!")
    return exit_status


def getUserIdFromTwitter(twitterUsername):
    api = get_twitter_api()
    if api:
        user = api.get_user(twitterUsername)
        return user.id_str


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
        Try to extract an username from a dict following pattern
           {'actor':
               {'username': 'xxxx'}
            }
         otherwise return None
    """
    decoded_data = extractPostData(request)
    if isinstance(decoded_data, dict):
        return decoded_data.get('actor', {}).get('username', None)
    return None


def rfc3339_parse(date):
    """
    Converts a date in format 2012-10-27T18:14:14.000Z to a python datetime
    """
    timeparts = list(re.search(r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+).?(\d*)Z', date).groups())
    timeparts[6] = timeparts[6] and (int(timeparts[6]) * 1000) or 0
    return datetime(*[int(part) for part in timeparts])


def date_filter_parser(date_filter):
    """
        Parses a date filter query in the following format:

        (+-)yyyy-(mm-dd)


        where month and day are optional, and a prefix may be specified to modifiy the query.
        Separators between year month and day can be anything except a number.

        If no +- modifier is specified, parser assumes it has to perform a exact query. If the
        + modifier is prepended, parser will generate query for dates earliear than specified,
        otherwise, if - is prepended, it will look for dates older than specified

        Examples:

            2014          Dates elapsed during year 2014
            2014-03       Dates elapsed during march of 2014
            +2014         Dates elapsed after the end of 2014
                          (anything Starting the first second of 2015, included)
            -2014-01-30   Dates elapsed before the begginning of the 30th of January 2014
                          (anything until 2014-01-29 at 23:59:59)

        At the end outputs a mongodb date query suitable to be set on any field
    """
    before = date_filter.startswith('-')
    after = date_filter.startswith('+')
    exact = not before and not after

    date_filter = date_filter.lstrip('-').lstrip('+')
    result = re.search(r'(\d{4})[^\d]*(\d{2})*[^\d]*(\d{2})*', date_filter)

    date1 = [0, 0, 0]
    date2 = [0, 0, 0]

    if result:
        year, month, day = result.groups()
        date1[0] = int(year)
        date2[0] = int(year)

        if month is not None:
            date1[1] = int(month)
            date2[1] = int(month)
        else:
            date1[1] = 1 if exact or before else 12
            if exact:
                date2[1] = 12

        if day is not None:
            date1[2] = int(day)
            date2[2] = int(day)
        else:
            last_day_of_month = monthrange(date1[0], date1[1])[1]
            date1[2] = 1 if exact or before else last_day_of_month
            if exact:
                date2[2] = last_day_of_month

        base_dt1 = datetime(*date1)
        if before:
            return {
                '$lt': datetime.combine(base_dt1, time.min)
            }
        if after:
            return {
                '$gt': datetime.combine(base_dt1, time.max)
            }
        if exact:
            base_dt2 = datetime(*date2)
            return {
                '$gte': datetime.combine(base_dt1, time.min),
                '$lte': datetime.combine(base_dt2, time.max)
            }

    return {}


def searchParams(request):
    """
        Extracts valid search params from the request, or sets default values if not found
        Returns a dict with all the results
        Raises InvalidSearchParams on bad param values
    """
    params = {}

    # KEEP For compatibility with older max, that did'nt distinguish
    # between sort order and sort priority. "sortBy" param will be translated
    # to sort_params

    deprecated_sort_by = request.params.get('sortBy', None)

    if deprecated_sort_by == 'activities':
        params['sort_strategy'] = 'published'
        params['sort_priority'] = 'activity'
    elif deprecated_sort_by == 'comments':
        params['sort_strategy'] = 'published'
        params['sort_priority'] = 'comments'
    elif deprecated_sort_by == 'likes':
        params['sort_strategy'] = 'likes'
        params['sort_priority'] = 'activity'
    elif deprecated_sort_by == 'flagged':
        params['sort_strategy'] = 'flagged'
        params['sort_priority'] = 'activity'

    sort_order = request.params.get('sort', None)
    if sort_order:
        params['sort_strategy'] = sort_order
        params['sort_priority'] = request.params.get('priority', 'activity')

    limit = request.params.get('limit', 10)
    try:
        limit = int(limit)
    except:
        raise InvalidSearchParams('limit must be a positive integer')
    else:
        if limit:
            params['limit'] = limit

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

    if 'date_filter' in request.params:
        date_filter = date_filter_parser(request.params.get('date_filter', ''))
        if date_filter:
            params['date_filter'] = date_filter

    hashtags = request.params.getall('hashtag')
    if hashtags:
        params['hashtag'] = [hasht.lower() for hasht in hashtags]

    actor = request.params.get('actor')
    if actor:
        params['actor'] = actor.lower().rstrip()

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
        params['tags'] = retags

    favorites = request.params.get('favorites')
    if asbool(favorites):
        params['favorites'] = request.actor.username

    context_tags = request.params.getall('context_tags')
    if context_tags:
        retags = []
        for tag in context_tags:
            retag = re.sub(r'\s*(\w+)\s*', r'\1', tag, re.UNICODE)
            if retag:
                retags.append(retag)
        params['context_tags'] = retags

    twitter_enabled = request.params.get('twitter_enabled')
    if twitter_enabled:
        params['twitter_enabled'] = twitter_enabled

    show_fields = request.params.get('show_fields')
    if show_fields:
        params['show_fields'] = re.findall(r'\w+', show_fields)

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
        newkey = key.lstrip('_')
        di[newkey] = di[key]
        del di[key]
        return newkey
    return key


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

    # Default is squashing anything or the specified fields in squash
    squash = kwargs.get('squash', [])
    preserve = kwargs.get('preserve', None)

    # If both parameters indicated, don't squash anything
    if 'preserve' in kwargs and 'squash' in kwargs:
        squash = []
    # If only preserved was indicated, squash
    elif preserve is not None:
        squash = set(di.keys()) - set(preserve)

    for key in di.keys():
        value = di[key]
        if isinstance(value, dict) or isinstance(value, list):
            di[key] = flatten(value, **kwargs)
        else:
            decodeBSONEntity(di, key)
        newkey = deUnderescore(di, key)
        if key in squash or newkey in squash:
            del di[newkey]
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
    if 'multipart/form-data' in request.content_type:
        try:
            json_data = json.loads(request.params.get('json_data'), object_hook=json_util.object_hook)
            if json_data.get('object', {}).get('objectType', '') in ['file', 'image']:
                json_data['object']['file'] = request.params.get('file')
        except:
            json_data = {}

    elif not 'multipart/form-data' in request.content_type and request.body:
        # Usually look for JSON encoded body, catch the case it does not contain
        # valid JSON data, e.g when uploading a file
        try:
            json_data = json.loads(request.body, object_hook=json_util.object_hook)
        except:
            json_data = {}
    else:
        json_data = {}

    return json_data
    # TODO: Do more syntax and format checks of sent data


def hasPermission(subscription, permission):
    """
        Determines if the subscription has a permission.
        If there's a revoked, permission this invalides any plain_permission.
        A granted permission oversees any revoke permission
    """
    permissions = subscription.get('permissions', [])
    has_plain_permission = permission in permissions
    has_granted_permission = permission in subscription.get('_grants', [])
    has_revoked_permission = permission in subscription.get('_grants', [])
    return (has_plain_permission and not has_revoked_permission) or has_granted_permission


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
            subsc = dict([(a[u_field], a) for a in actor.get(context.user_subscription_storage, {})])
            subscriptions.update(subsc)
            subscription = subscriptions.get(context.getIdentifier(), None)
            if subscription is None:
                raise Unauthorized("You are not subscribed to this context : %s" % context.getIdentifier())

        # If user is trying to post on a subscribed context/s
        # Check that has write permission in all the contexts

        allowed_to_write = hasPermission(subscription, 'write')
        if not allowed_to_write:
            raise Unauthorized("You are not allowed to post to this context : %s" % context.getIdentifier())

    # If we reached here, we have permission to post on all contexts
    return True


def canReadContext(actor, url):
    """ DEPRECATED
    """
    # If no context filter defined, write/read is always allowed
    if url == []:
        return True

    subscribed_contexts_urls = [a['object']['url'] for a in actor['subscribedTo'] if hasPermission(a['permissions'], 'read')]

    if url not in subscribed_contexts_urls:

        # Check recursive read: User is allowed to read recursively on an
        # unsubscribed context if is subscribed to at least one child context
        containments = [usc.startswith(url) for usc in subscribed_contexts_urls]
        if True not in containments:
            raise Unauthorized("You are not subscribed to this context: %s" % url)

    #If we reached here, we have permission to read on all contexts
    return True


def rotate_image_by_EXIF(image):
    """
        Images with rotation will have a value in field 274. If we don't know how much
        we have to rotate or we don't have the value, will make no changes to the image.
    """
    exif_data = image._getexif() if hasattr(image, '_getexif') else {}
    exif_rotation_identifier = exif_data.get(274, None) if isinstance(exif_data, dict) else None
    exif_rotation = EXIF_ROTATIONS.get(exif_rotation_identifier, 0)

    if exif_rotation:
        return image.rotate(exif_rotation)
    return image
