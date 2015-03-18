# -*- coding: utf-8 -*-
import venusian


class endpoint(object):
    """
        Custom decorator for max oauth2 endpoints
        Stolen from pyramid.view.view_config
    """
    venusian = venusian  # for testing injection

    def __init__(self, **settings):
        if 'for_' in settings:
            if settings.get('context') is None:
                settings['context'] = settings['for_']
        self.__dict__.update(settings)

    def __call__(self, wrapped):
        settings = self.__dict__.copy()
        depth = settings.pop('_depth', 0)

        def callback(context, name, ob):

            config = context.config.with_package(info.module)
            config.add_view(view=ob, **settings)

        def max_wrapper(func):
            def replacement(*args, **kwargs):
                return func(*args, **kwargs)
            return replacement

        # pre-decorate original method before passing it to venusian
        rewrapped = max_wrapper(wrapped)

        # patch decorated info to preserver name and doc
        rewrapped.__name__ = wrapped.__name__
        rewrapped.__doc__ = wrapped.__doc__

        # effectively apply the @endpoint decorator
        info = self.venusian.attach(rewrapped, callback, category='max',
                                    depth=depth + 1)

        # Modify codeinfo to preserver original wrapper method name
        info.codeinfo = info.codeinfo[:-1] + ('@endpoint.{}'.format(wrapped.__name__),)

        if info.scope == 'class':
            # if the decorator was attached to a method in a class, or
            # otherwise executed at class scope, we need to set an
            # 'attr' into the settings if one isn't already in there
            if settings.get('attr') is None:
                settings['attr'] = wrapped.__name__

        settings['_info'] = info.codeinfo  # fbo "action_method"
        return rewrapped
