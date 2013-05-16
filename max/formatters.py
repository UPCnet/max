# -*- coding: utf-8 -*-
from max.regex import RE_VALID_HASHTAG
from max.regex import RE_VALID_TWITTER_USERNAME
import re
import bleach


def stripHash(text):
    """
        Returns the valid part of a hashtag input, lowercased
    """
    return re.sub(RE_VALID_HASHTAG, r'\1', text).lower()


def stripTwitterUsername(text):
    """
        Returns the valid part of a twitter username input, lowercased
    """
    return re.sub(RE_VALID_TWITTER_USERNAME, r'\1', text).lower()


def stripHTMLTags(text):
    """
        Strips unwanted html tags. Allows bleach defaults except li, ol and ul
    """

    ALLOWED_TAGS = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'strong']
    return bleach.clean(text, strip=True, tags=ALLOWED_TAGS)
