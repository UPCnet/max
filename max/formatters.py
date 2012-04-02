from max.regex import RE_VALID_HASHTAG
import re


def stripHash(text):
    """
    """
    return re.sub(RE_VALID_HASHTAG, text, '')
