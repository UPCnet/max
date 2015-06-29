# -*- coding: utf-8 -*-
from zope.interface import providedBy

from max.deprecations import DELETE_DEPRECATIONS
from max.deprecations import POST_DEPRECATIONS
from max.deprecations import check_deprecation
from max.exceptions.http import JSONHTTPPreconditionFailed
from max.exceptions.scavenger import format_raw_request
from max.exceptions.scavenger import format_raw_response

from pyramid.interfaces import IExceptionViewClassifier
from pyramid.interfaces import IRequest
from pyramid.interfaces import IView

from pymongo.errors import AutoReconnect
from urllib import unquote_plus

import logging
import signal
import sys
import json
import traceback

request_logger = logging.getLogger('requestdump')
dump_requests = {'enabled': False}

SEPARATOR = '-' * 80
DUMP_TEMPLATE = u"""
{sep}
{{}}
--
{{}}
{sep}
""".format(sep=SEPARATOR)


def set_signal():
    def toggle_request_dump(*args):
        dump_requests['enabled'] = not dump_requests['enabled']
        request_logger.debug(u'{}abling request dumper'.format('En' if dump_requests['enabled'] else 'Dis'))
    signal.signal(signal.SIGUSR1, toggle_request_dump)


def dump_request(request, response):
    """
        Logs formatted request + response to request_dump logger
        if global var dump_requests['enabled'] is True
    """
    if dump_requests['enabled'] and response.status_int != 500:
        request_logger.debug(DUMP_TEMPLATE.format(
            format_raw_request(request),
            format_raw_response(response)
        ))


def excview_tween_factory(handler, registry):
    """ A :term:`tween` factory which produces a tween that catches an
    exception raised by downstream tweens (or the main Pyramid request
    handler) and, if possible, converts it into a Response using an
    :term:`exception view`."""
    adapters = registry.adapters

    def excview_tween(request):
        attrs = request.__dict__

        def handle_exception(catched_exc):
            # WARNING: do not assign the result of sys.exc_info() to a local
            # var here, doing so will cause a leak.  We used to actually
            # explicitly delete both "exception" and "exc_info" from ``attrs``
            # in a ``finally:`` clause below, but now we do not because these
            # attributes are useful to upstream tweens.  This actually still
            # apparently causes a reference cycle, but it is broken
            # successfully by the garbage collector (see
            # https://github.com/Pylons/pyramid/issues/1223).
            attrs['exc_info'] = sys.exc_info()
            attrs['exception'] = catched_exc
            # clear old generated request.response, if any; it may
            # have been mutated by the view, and its state is not
            # sane (e.g. caching headers)
            if 'response' in attrs:  # pragma: no cover
                del attrs['response']
            # we use .get instead of .__getitem__ below due to
            # https://github.com/Pylons/pyramid/issues/700
            request_iface = attrs.get('request_iface', IRequest)
            provides = providedBy(catched_exc)
            for_ = (IExceptionViewClassifier, request_iface.combined, provides)
            view_callable = adapters.lookup(for_, IView, default=None)
            if view_callable is None:  # pragma: no cover
                raise
            return view_callable(catched_exc, request)

        try:
            response = handler(request)
        except AutoReconnect as exc:
            tryin_to_reconnect = True
            while tryin_to_reconnect:
                try:
                    response = handler(request)
                except AutoReconnect:
                    pass
                # This except gets a pragma, because it seems that is executed in another frame and
                # is not catched by coverage module
                except Exception as exc:  # pragma: no cover
                    tryin_to_reconnect = False
                    response = handle_exception(exc)
                else:
                    tryin_to_reconnect = False

        except Exception as exc:
            response = handle_exception(exc)

        dump_request(request, response)
        return response

    return excview_tween


def compatibility_checker_factory(handler, registry):
    def compatibility_checker_tween(request):
        requested_compat_id = request.headers.get('X-Max-Compat-ID', None)
        if requested_compat_id is None:
            response = handler(request)
            return response

        expected_compat_id = str(request.registry.settings.get('max.compat_id'))
        if expected_compat_id == requested_compat_id:
            response = handler(request)
            return response
        else:
            return JSONHTTPPreconditionFailed(
                error=dict(
                    objectType='error',
                    error="CompatibilityIDMismatch",
                    error_description='X-Max-Compat-ID header value mismatch, {} was expected'.format(expected_compat_id)))
    return compatibility_checker_tween


def post_tunneling_factory(handler, registry):
    def post_tunneling_tween(request):
        original_body = request.body
        # Look for header in post-data if not found in headers
        overriden_method = request.headers.get('X-HTTP-Method-Override', request.params.get('X-HTTP-Method-Override', None))
        is_valid_overriden_method = overriden_method in ['DELETE', 'PUT', 'GET']
        is_POST_request = request.method.upper() == 'POST'
        if is_POST_request and is_valid_overriden_method:
            # If it's an overriden GET pass over the authentication data in the post body
            # to the headers, before overriding the method, after this, post data will be lost
            if overriden_method == 'GET':
                request.headers.setdefault('X-Oauth-Token', request.params.get('X-Oauth-Token', ''))
                request.headers.setdefault('X-Oauth-Username', request.params.get('X-Oauth-Username', ''))
                request.headers.setdefault('X-Oauth-Scope', request.params.get('X-Oauth-Scope', ''))

            request.method = overriden_method

        # Restore uncorrupted body
        request.body = original_body
        response = handler(request)
        return response
    return post_tunneling_tween


def deprecation_wrapper_factory(handler, registry):
    def deprecation_wrapper_tween(request):
        response_wrapper = None
        if request.method == 'POST':
            for pattern, action in POST_DEPRECATIONS:
                matched, response_wrapper = check_deprecation(request, pattern, action)
                if matched:
                    break
        elif request.method == 'DELETE':
            for pattern, action in DELETE_DEPRECATIONS:
                matched, response_wrapper = check_deprecation(request, pattern, action)
                if matched:
                    break
        response = handler(request)
        if response_wrapper:
            return response_wrapper(response)
        else:
            return response
    return deprecation_wrapper_tween


import os
REPORT_BASE = '/tmp/mongo_probe'


def mongodb_probe_factory(handler, registry):
    def mongodb_probe_tween(request):
        if not hasattr(request, 'mongodb_probe'):
            request.mongodb_probe = {
                'cursors': {},
                'cursor_count': 0
            }

        response = handler(request)
        if request.matched_route:
            endpoint = request.matched_route.path.strip('/').replace('/', '_')
            method = request.method
            request_folder = '{}/{}___{}'.format(REPORT_BASE, endpoint, method)
            if not os.path.exists(request_folder):
                os.makedirs(request_folder)
            count = len(os.listdir(request_folder))
            request_queries = []
            for cursorid, cursor in sorted(request.mongodb_probe.get('cursors', []).items(), key=lambda x: x[1]['order']):
                del cursor['order']
                del cursor['used']
                request_queries.append(cursor)

            output = {
                'queries': request_queries,
                'request': request.url
            }

            test_name = [a[2] for a in traceback.extract_stack() if a[2].startswith('test_')]
            if test_name:
                output['test'] = test_name

            open('{}/{}'.format(request_folder, count), 'w').write(json.dumps(output, indent=4))

        return response
    return mongodb_probe_tween


def browser_debug_factory(handler, registry):
    def browser_debug_tween(request):
        debug = request.params.get('d', None)
        debugging = debug is not None
        if debugging:
            user = request.params.get('u', None)
            token = request.params.get('t', 'fake_token')
            method = request.params.get('m', '').upper()
            payload = request.params.get('p', None)

            if user:
                new_headers = {
                    'X-Oauth-Token': token,
                    'X-Oauth-Username': user,
                    'X-Oauth-Scope': 'widgetcli'
                }
                request.headers.update(new_headers)

                if method in ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']:
                    request.method = method.upper()

                if payload:
                    request.text = payload

        request.body = unquote_plus(request.body).strip('=')
        request.headers['Content-Type'] = 'application/json'
        response = handler(request)

        if debug == '1' and user:
            response.content_type = 'text/html'
            response.text = u'<html><body>{}</body></html>'.format(response.text)
        return response

    return browser_debug_tween
