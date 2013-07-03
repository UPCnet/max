# -*- coding: utf-8 -*-

"""
    A valid hashtag is a string of alphanumeric chars or _-
    A valid hashtag has ONE char minimum length and no length limit
    A valid hashtag MAY have a # at the beginning.
    A valid hashtag doesn't contain preceding nor trailing whitespace.
    The capture parenthesis strips @ and whitespace, and leaves real hashtag as input
"""
RE_VALID_HASHTAG = r'^\s*#?([a-zA-Z0-9_-]+)\s*$'


"""
    A valid twitter username is a string of alphanumeric chars or _
    A valid twitter username has ONE char minimum length and FIFTEEN chars maximum length
    A valid twitter username MAY have a @ at the beginning.
    A valid twitter username doesn't contain preceding nor trailing whitespace.
    The capture parenthesis strips @ and whitespace, and leaves real username as input
"""
RE_VALID_TWITTER_USERNAME = r'^\s*@?([a-zA-Z0-9_]{1,15})\s*$'

"""
    A valid IOS token is a string of alphanumeric chars
    A valid IOS token has EXACTLY THIRTY TWO chars length
    A valid IOS token doesn't contain preceding nor trailing whitespace.
    The capture parenthesis strips whitespace, and leaves the token as input
"""
RE_VALID_IOS_TOKEN = r'^\s*([a-zA-Z0-9]{32})\s*$'
