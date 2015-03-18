import inspect


def marmoset_patch(old, new, extra_globals={}):
    g = old.func_globals
    g.update(extra_globals)
    c = inspect.getsource(new)
    exec c in g
    old.im_func.func_code = g[new.__name__].func_code


# Patch to disable requests logging on gevent
def log_request(self):  # pragma: no cover
    pass

try:
    from gevent.pywsgi import WSGIHandler
except:
    pass
else:
    marmoset_patch(WSGIHandler.log_request, log_request)
