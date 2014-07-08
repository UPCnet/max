#Patch to get the real function name on multiple-decorated functions
import venusian


def attach(wrapped, callback, **kwargs):
    """
        Generic patch to venusian attach().

        Calls original attach() method, with increased depth, (as we are adding an extra
        function call to the tracback), and returns a modified instance of AttachInfo with
        patched codeinfo information reflecting the real function name.

    """
    kwargs.setdefault('category', None)
    kwargs.setdefault('depth', 1)
    kwargs.setdefault('name', None)

    kwargs['depth'] += 1

    attach_info = venusian.original_attach(wrapped, callback, **kwargs)
    new_codeinfo = attach_info.codeinfo[:-1] + (wrapped.func_name,)
    attach_info.codeinfo = new_codeinfo
    return attach_info

venusian.original_attach = venusian.attach
venusian.attach = attach
