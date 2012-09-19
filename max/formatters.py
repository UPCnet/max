# -*- coding: utf-8 -*-
from max.regex import RE_VALID_HASHTAG
from max.regex import RE_VALID_TWITTER_USERNAME
import re


def stripHash(text):
    """
        Returns the valid part of a hashtag input
    """
    return re.sub(RE_VALID_HASHTAG, r'\1', text)


def stripTwitterUsername(text):
    """
        Returns the valid part of a twitter username input
    """
    return re.sub(RE_VALID_TWITTER_USERNAME, r'\1', text)
