#Patch to get the real function name on multiple-decorated functions
import venusian
from venusian import AttachInfo
from venusian import ATTACH_ATTR
from venusian import Categories
from venusian.advice import getFrameInfo
import sys


def attach(wrapped, callback, category=None, depth=1):
    """ Attach a callback to the wrapped object.  It will be found
    later during a scan.  This function returns an instance of the
    :class:`venusian.AttachInfo` class."""
    frame = sys._getframe(depth + 1)
    scope, module, f_locals, f_globals, codeinfo = getFrameInfo(frame)
    module_name = getattr(module, '__name__', None)
    if scope == 'class':
        # we're in the midst of a class statement
        categories = f_locals.setdefault(ATTACH_ATTR, Categories(None))
        callbacks = categories.setdefault(category, [])
        callbacks.append((callback, module_name))
    else:
        categories = getattr(wrapped, ATTACH_ATTR, None)
        if categories is None or not categories.attached_to(wrapped):
            # if there aren't any attached categories, or we've retrieved
            # some by inheritance, we need to create new ones
            categories = Categories(wrapped)
            setattr(wrapped, ATTACH_ATTR, categories)
        callbacks = categories.setdefault(category, [])
        callbacks.append((callback, module_name))
        codeinfo = codeinfo[:-1] + (wrapped.func_name,)
    return AttachInfo(
        scope=scope, module=module, locals=f_locals, globals=f_globals,
        category=category, codeinfo=codeinfo)

venusian.attach = attach
