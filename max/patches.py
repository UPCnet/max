import inspect
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
        if not hasattr(request, 'mongodb_probe'):
            request.mongodb_probe = {}

        request.mongodb_probe.setdefault('cursors', {})
        request.mongodb_probe.setdefault('cursor_count', 0)
        return request.mongodb_probe


def patched_Cursor__init__(self, collection, spec, *args, **kwargs):
    original_Cursor__init__(self, collection, spec, *args, **kwargs)
    if collection.name not in IGNORE_COLLECTIONS:
        probe_data = get_probe_data()
        if probe_data:
            cursor_id = id(self)
            probe_data['cursors'][cursor_id] = {
                'used': False,
                'collection': collection.name,
                'spec': spec,
                'order': probe_data['cursor_count']
            }
            probe_data['cursor_count'] += 1


def patched_Cursornext(self):
    probe_data = get_probe_data()
    if probe_data:
        cursor_id = id(self)
        if cursor_id in probe_data['cursors']:
            if probe_data['cursors'][cursor_id]['collection'] == 'activity':
                import ipdb;ipdb.set_trace()
            if not probe_data['cursors'][cursor_id]['used']:
                probe_data['cursors'][cursor_id]['used'] = True

    data = original_Cursornext(self)
    return data

Cursor.__init__ = patched_Cursor__init__
Cursor.next = patched_Cursornext
