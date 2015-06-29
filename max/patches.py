import inspect
import traceback
import re
from pyramid.threadlocal import get_current_request


def marmoset_patch(old, new, extra_globals={}):  # pragma: no cover
    """
        Patch to disable requests logging when running on gevent
    """
    g = old.func_globals
    g.update(extra_globals)
    c = inspect.getsource(new)
    exec c in g
    old.im_func.func_code = g[new.__name__].func_code


def log_request(self):  # pragma: no cover
    pass

try:
    from gevent.pywsgi import WSGIHandler
except:
    pass
else:
    marmoset_patch(WSGIHandler.log_request, log_request)  # pragma: no cover


from pymongo.cursor import Cursor
original_Cursor__init__ = Cursor.__init__
original_Cursornext = Cursor.next


IGNORE_COLLECTIONS = ['$cmd']


def get_probe_data():
    request = get_current_request()
    if request:
        return request.mongodb_probe


def get_originator():
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

from copy import deepcopy
from datetime import datetime


def format_spec(spec):
    from_spec = deepcopy(spec)
    newspec = {}

    def format_value(value):
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, list):
            newlist = []
            for item in value:
                newlist.append(format_value(item))
            return newlist
        elif isinstance(value, dict):
            newdict = []
            for itemkey, item in value.items():
                newdict[itemkey] = format_value(item)
            return newdict
    for key, value in from_spec.items:
        newspec[key] = format_value(value)

    return newspec


def patched_Cursor__init__(self, collection, spec={}, *args, **kwargs):
    original_Cursor__init__(self, collection, spec, *args, **kwargs)
    if collection.name not in IGNORE_COLLECTIONS:
        probe_data = get_probe_data()
        if probe_data:
            cursor_id = id(self)
            probe_data['cursors'][cursor_id] = {
                'used': False,
                'collection': collection.name,
                'spec': format(spec),
                'order': probe_data['cursor_count']
            }
            probe_data['cursor_count'] += 1


def patched_Cursornext(self):
    probe_data = get_probe_data()
    if probe_data:
        cursor_id = id(self)
        if cursor_id in probe_data['cursors']:
            if not probe_data['cursors'][cursor_id]['used']:
                probe_data['cursors'][cursor_id]['used'] = True
                probe_data['cursors'][cursor_id]['originator'] = get_originator()

    data = original_Cursornext(self)
    return data


def enable_mongodb_probe():
    Cursor.__init__ = patched_Cursor__init__
    Cursor.next = patched_Cursornext
