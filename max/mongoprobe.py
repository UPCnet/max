# -*- coding: utf-8 -*-
from pyramid.threadlocal import get_current_request

from copy import deepcopy
from datetime import datetime
from hashlib import sha1
from pymongo.cursor import Cursor
from pyramid.settings import asbool

import json
import os
import re
import traceback

original_Cursor__init__ = Cursor.__init__
original_Cursornext = Cursor.next

IGNORE_COLLECTIONS = ['$cmd']
REQUEST_REPORT = '/tmp/mongo_probe/requests'
QUERIES_REPORT = '/tmp/mongo_probe/queries'


def get_probe_data():
    """
        Get probe data from current request
    """
    request = get_current_request()
    if request:
        return request.mongodb_probe


def get_originator():
    """
        Get clean traceback of which max code originated the pymongo query.
    """
    stack = traceback.extract_stack()
    clean = []

    for file, line, method, code in stack[::-1]:
        if 'max/max' not in file:
            continue
        if file.endswith('patches.py'):
            continue
        module = re.search('src/max/(.*?)\.py', file).groups()[0].replace('/', '.')
        if module in ['max.tweens']:
            break
        mid = '{}.{}:{}'.format(module, method, line)
        clean.append(mid)
    clean = clean[::-1]
    return clean


def format_spec(spec, normalize=False):
    """
        Formats a pymongo query to json-friendly values.

        When normalize is True, all values different than dicts
        and lists will be normalized to a mock 'VALUE', to be able
        to identify similar queries that only differ in particular values
    """
    from_spec = deepcopy(spec)
    newspec = {}

    def _format(value):
        if normalize:
            return 'VALUE'
        else:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, unicode):
                return value.encode('utf-8')
            else:
                return str(value)

    def format_value(value, normalize=False):
        if isinstance(value, list):
            newlist = []
            for item in value:
                newvalue = format_value(item)
                # When normalizing, do not add a value to a list if it's already in
                # This way all plain value lists will remain the same
                if normalize is False or (normalize is True and newvalue not in newlist):
                    newlist.append(newvalue)
            return newlist
        elif isinstance(value, dict):
            newdict = {}
            for itemkey, item in value.items():
                newdict[itemkey] = format_value(item)
            return newdict
        else:
            return _format(value)

    for key, value in from_spec.items():
        newspec[key] = format_value(value)

    return newspec


def patched_Cursor__init__(self, collection, spec={}, *args, **kwargs):
    """
        Patch for Cursor initialization.

        It takes care of creating the probe entry for this cursor, that will be
        populated on the next patch
    """
    original_Cursor__init__(self, collection, spec, *args, **kwargs)
    if collection.name not in IGNORE_COLLECTIONS:
        probe_data = get_probe_data()
        if probe_data:
            cursor_id = id(self)
            normalized_spec = format_spec(spec, normalize=True)
            cursor_hash = sha1(json.dumps(normalized_spec)).hexdigest()

            probe_data['cursors'][cursor_id] = {
                'used': False,
                'collection': collection.name,
                'spec': normalized_spec,
                'hash': cursor_hash,
                'order': probe_data['cursor_count']
            }
            probe_data['cursor_count'] += 1


def patched_Cursornext(self):
    """
        Patch for the next iterator method of Cursor.

        The first invocation of Cursor.next() is the one that fetches data from
        mongodb, so we get the originating traceback here.
    """
    probe_data = get_probe_data()
    if probe_data:
        cursor_id = id(self)
        if cursor_id in probe_data['cursors']:
            if not probe_data['cursors'][cursor_id]['used']:
                probe_data['cursors'][cursor_id]['used'] = True
                probe_data['cursors'][cursor_id]['originator'] = get_originator()

    data = original_Cursornext(self)
    return data


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
            request_folder = '{}/{}___{}'.format(REQUEST_REPORT, endpoint, method)
            if not os.path.exists(request_folder):
                os.makedirs(request_folder)
            count = len(os.listdir(request_folder))
            request_queries = []
            for cursorid, cursor in sorted(request.mongodb_probe.get('cursors', []).items(), key=lambda x: x[1]['order']):
                del cursor['order']
                del cursor['used']
                request_queries.append(cursor)
                if not os.path.exists(QUERIES_REPORT):
                    os.makedirs(QUERIES_REPORT)
                if not os.path.exists('{}/{collection}_{hash}'.format(QUERIES_REPORT, **cursor)):
                    dumped = deepcopy(cursor)
                    del dumped['originator']
                    del dumped['hash']
                    open('{}/{collection}_{hash}'.format(QUERIES_REPORT, **cursor), 'w').write(json.dumps(dumped, indent=4))

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


def setup(settings):
    """
        Enable mongo probe patches and tweens
    """
    if asbool(settings.get('max.enable_mongodb_probe', False)) or asbool(os.environ.get('mongoprobe', False)):
        settings['pyramid.tweens'].insert(1, 'max.mongoprobe.mongodb_probe_factory')
        Cursor.__init__ = patched_Cursor__init__
        Cursor.next = patched_Cursornext
