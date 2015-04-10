# -*- coding: utf-8 -*-
from datetime import datetime
from hashlib import sha1

import json
import logging
import re
import traceback

logger = logging.getLogger('exceptions')
request_logger = logging.getLogger('requestdump')
dump_requests = {'enabled': False}


ERROR_TEMPLATE = u"""
------------------------------------------------
BEGIN EXCEPTION REPORT: {hash}
MATCHED_ROUTE: {matched_route}
DATE: {time}
REQUEST:

{raw_request}

TRACEBACK:

{traceback}

END EXCEPTION REPORT
------------------------------------------------
"""


def format_raw_request(request):
    """
        Formats raw request. Replaces images with a tag to avoid log flood and errors
        returns an error string if not able to parse request
    """
    raw_request = request.as_bytes()
    content_type = request.headers.get('Content-Type', '')
    try:
        if 'multipart/form-data' in content_type:
            boundary = re.search(r"boundary\s*=\s*(.*?)$", content_type).groups()[0]
            boundary = boundary.replace('$', r'\$')
            match = re.search(r'\r\n(?:.*?Content-type:\s*image.*?)\r\n\r\n(.*?){}'.format(boundary), raw_request, re.DOTALL | re.IGNORECASE)
            if match:
                image = match.groups()[0]
                raw_request = raw_request.replace(image, '<Image data {} bytes>\r\n'.format(len(image)))

        raw_request.decode('utf-8')

    except UnicodeDecodeError as unicode_error:
        return raw_request[:unicode_error.start] + u"\r\n*** Unicode Decode Error parsing request, request trunked at byte {} ***\r\n".format(unicode_error.start)
    except Exception:
        return u"\r\n*** Error parsing request ***\r\n\r\n{}\r\n*** End traceback ***".format(traceback.format_exc())

    return raw_request


def format_raw_response(response):
    """
        Formats a raw response. Replaces images with a tag to avoid log flood errors.
        Returns an error string if not able to parse request
    """
    headers = u'\n'.join([u'{}: {}'.format(*header) for header in response.headers.items()])

    has_image = re.search(r'Content-type:\s*image', headers, re.DOTALL | re.IGNORECASE)
    if has_image:
        body = u'<Image data {} bytes>'.format(len(response.body))
    else:
        body = response.ubody

    raw_response = u'{}\n{}\n\n{}'.format(response.status, headers, body)
    return raw_response


def saveException(request, error):
    """
        Logs the exception

    """
    time = datetime.now().isoformat()
    matched_route = request.matched_route.name if request.matched_route else 'No route matched'
    matchdict = request.matchdict or []

    entry = dict(
        traceback=error,
        time=time,
        raw_request=format_raw_request(request),
        matched_route=matched_route,
        matchdict=matchdict,
    )

    dump = json.dumps(entry)
    entry['hash'] = sha1(dump).hexdigest()
    exception_log = ERROR_TEMPLATE.format(**entry)
    logger.debug(exception_log)
    return entry['hash'], exception_log
