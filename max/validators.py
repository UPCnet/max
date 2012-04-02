import re
from max.regex import RE_VALID_HASHTAG


def isValidHashtag(text):
    """
        A valid hashtag is a word whithout whitespaces and without inline '#'
        A hashtag MAY begin with ONE '#', or not.
    """
    return re.match(RE_VALID_HASHTAG, text)
