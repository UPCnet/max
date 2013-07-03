import re
from max.regex import RE_VALID_HASHTAG
from max.regex import RE_VALID_TWITTER_USERNAME
from max.regex import RE_VALID_IOS_TOKEN

"""
    Validators accept ONE parameter containing the value of the field to be validated
    Validators respond with a 2-element tuple (success, message)

    - success MUST be a boolean indicating were the validation succeded or not
    - message MUST be a message indicating a description of why the validation didn't succeded
"""


def isValidHashtag(text, message='Invalid hashtag'):
    """
        Is a valid hashtag?
        See max.regex for more info on the regex
    """
    match = re.match(RE_VALID_HASHTAG, text)
    success = match is not None
    return (success, message)


def isValidTwitterUsername(text, message='Invalid twitter username'):
    """
        Is a valid twitter username?
        See max.regex for more info on the regex
    """
    match = re.match(RE_VALID_TWITTER_USERNAME, text)
    success = match is not None
    return (success, message)


def isValidIOSToken(text, message='Invalid IOS token'):
    """
        Is a valid IOS token?
        See max.regex for more info on the regex
    """
    match = re.match(RE_VALID_IOS_TOKEN, text)
    success = match is not None
    return (success, message)
