# -*- coding: utf-8 -*-
import json
import re
import requests
import urllib2

UNICODE_ACCEPTED_CHARS = u'áéíóúàèìòùïöüçñ'

FIND_URL_REGEX = r'((https?\:\/\/)|(www\.))(\S+)(\w{2,4})(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?'
FIND_HASHTAGS_REGEX = r'(\s|^)#{1}([\w\-\_\.%s]+)' % UNICODE_ACCEPTED_CHARS
FIND_KEYWORDS_REGEX = r'(\s|^)(?:#|\'|\"|\w\')?([\w\-\_\.%s]{3,})[\"\']?' % UNICODE_ACCEPTED_CHARS


def formatMessageEntities(request, text):
    """
        function that shearches for elements in the text that have to be formatted.
        Currently shortens urls.
    """

    def shorten(matchobj):
        url = matchobj.group(0)
        return shortenURL(url, secure=request.url.startswith('https://'))

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


def shortenURL(url, secure=False):
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
            url = response.get('data', {}).get('url', queryurl)
            if secure:
                url.replace('http://', 'https://')
    except:
        url = queryurl

    return url
