# -*- coding: utf-8 -*-
from max.resources import Root

from pyramid.response import Response
from pyramid.view import view_config

import venusian

@view_config(context=Root)
def rootView(context, request):

    message = 'I am a max server'
    response = Response(message)
    return response


class endpoint(object):
    """ A function, class or method :term:`decorator` which allows a
    developer to create view registrations nearer to a :term:`view
    callable` definition than use :term:`imperative
    configuration` to do the same.

    For example, this code in a module ``views.py``::

      from resources import MyResource

      @view_config(name='my_view', context=MyResource, permission='read',
                   route_name='site1')
      def my_view(context, request):
          return 'OK'

    Might replace the following call to the
    :meth:`pyramid.config.Configurator.add_view` method::

       import views
       from resources import MyResource
       config.add_view(views.my_view, context=MyResource, name='my_view',
                       permission='read', route_name='site1')

    .. note: :class:`pyramid.view.view_config` is also importable, for
             backwards compatibility purposes, as the name
             :class:`pyramid.view.bfg_view`.

    :class:`pyramid.view.view_config` supports the following keyword
    arguments: ``context``, ``permission``, ``name``,
    ``request_type``, ``route_name``, ``request_method``, ``request_param``,
    ``containment``, ``xhr``, ``accept``, ``header``, ``path_info``,
    ``custom_predicates``, ``decorator``, ``mapper``, ``http_cache``,
    ``match_param``, ``csrf_token``, ``physical_path``, and ``predicates``.

    The meanings of these arguments are the same as the arguments passed to
    :meth:`pyramid.config.Configurator.add_view`.  If any argument is left
    out, its default will be the equivalent ``add_view`` default.

    An additional keyword argument named ``_depth`` is provided for people who
    wish to reuse this class from another decorator.  The default value is
    ``0`` and should be specified relative to the ``view_config`` invocation.
    It will be passed in to the :term:`venusian` ``attach`` function as the
    depth of the callstack when Venusian checks if the decorator is being used
    in a class or module context.  It's not often used, but it can be useful
    in this circumstance.  See the ``attach`` function in Venusian for more
    information.

    .. seealso::

        See also :ref:`mapping_views_using_a_decorator_section` for
        details about using :class:`pyramid.view.view_config`.

    .. warning::

        ``view_config`` will work ONLY on module top level members
        because of the limitation of ``venusian.Scanner.scan``.

    """
    venusian = venusian # for testing injection

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

        def decorator2(func):
            def replacement(*args, **kwargs):
                return func(*args, **kwargs)
            return replacement

        rewrapped = decorator2(wrapped)
        info = self.venusian.attach(rewrapped, callback, category='pyramid',
                                    depth=depth + 1)

        if info.scope == 'class':
            # if the decorator was attached to a method in a class, or
            # otherwise executed at class scope, we need to set an
            # 'attr' into the settings if one isn't already in there
            if settings.get('attr') is None:
                settings['attr'] = wrapped.__name__

        settings['_info'] = info.codeinfo # fbo "action_method"
        return rewrapped
