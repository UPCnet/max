# -*- coding: utf-8 -*-
import json
import re
import requests
import urllib2
from max.resources import getMAXSettings

UNICODE_ACCEPTED_CHARS = u'áéíóúàèìòùïöüçñ'

# Inicialmente Carles habia puesto este regex FIND_URL_REGEX = r'((https?\:\/\/)|(www\.))(\S+)(\w{2,4})(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?'
# pero nos da problemas con la url: http://www.businessinsider.com/r-for-egypts-entrepreneurs-going-green-makes-business-sense-2016-6
# Hemos dejado este regex en FIND_URL_KEYWORDS_REGEX para el findKeywords que no tenemos claro para que sirve
FIND_URL_REGEX = r'((https?\:\/\/)|(www\.))(\S+)'
FIND_URL_KEYWORDS_REGEX = r'((https?\:\/\/)|(www\.))(\S+)(\w{2,4})(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?'
FIND_HASHTAGS_REGEX = r'(\s|^)#{1}([\w\-\_\.%s]+)' % UNICODE_ACCEPTED_CHARS
FIND_KEYWORDS_REGEX = r'(\s|^)(?:#|\'|\"|\w\')?([\w\-\_\.%s]{3,})[\"\']?' % UNICODE_ACCEPTED_CHARS


def formatMessageEntities(request, text):
    """
        function that shearches for elements in the text that have to be formatted.
        Currently shortens urls.
    """

    def shorten(matchobj):
        url = matchobj.group(0)
        settings = getMAXSettings(request)
        bitly_username = settings.get('max_bitly_username', '')
        bitly_api_key = settings.get('max_bitly_api_key', '')

        return shortenURL(url, bitly_username, bitly_api_key, secure=request.url.startswith('https://'))

    shortened = re.sub(FIND_URL_REGEX, shorten, text, flags=re.IGNORECASE)

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
    stripped_urls = re.sub(FIND_URL_KEYWORDS_REGEX, '', _text)
    keywords = [kw.groups()[1] for kw in re.finditer(FIND_KEYWORDS_REGEX, stripped_urls)]
    return keywords


def shortenURL(url, bitly_username, bitly_api_key, secure=False):
    """
        Shortens a url using bitly API. Keeps the original url in case
        something goes wrong with the api call
    """
    # FOR DEBUGGING !! if localhost present in the domain part of the url,
    # substitute with a fake domain
    # to allow bitly shortening in development environments
    # (localhost/ port not allowed in URI by bitly api)
    shortened_url = re.sub(r'(.*://)(localhost:[0-9]{4,5})(.*)', r'\1foo.bar\3', url)

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
            shortened_url = response.get('data', {}).get('url', queryurl)
            if secure:
                shortened_url = shortened_url.replace('http://', 'https://')
    except:
        shortened_url = url

    return shortened_url
