# -*- coding: utf-8 -*-
from datetime import datetime
from pyramid.response import Response
from types import GeneratorType

from max.MADMax import ResultsWrapper
from max.utils.dates import datetime_to_rfc3339

import json
import venusian


class endpoint(object):
    """
        Custom decorator for max oauth2 endpoints
        Stolen from pyramid.view.view_config
    """
    venusian = venusian  # for testing injection
    modifiers = []

    def __init__(self, **settings):
        if 'for_' in settings:
            if settings.get('context') is None:  # pragma: no cover
                settings['context'] = settings['for_']
        self.__dict__.update(settings)

    def __call__(self, wrapped):
        settings = self.__dict__.copy()
        depth = settings.pop('_depth', 0)
        modifiers = settings.pop('modifiers', [])

        def callback(context, name, ob):
            ob.modifiers = modifiers
            config = context.config.with_package(info.module)
            config.add_view(view=ob, **settings)

        info = self.venusian.attach(wrapped, callback, category='max',
                                    depth=depth + 1)

        # Fix multiline decorator signature in code object
        decorator_name = '@{}'.format(self.__class__.__name__)
        if decorator_name not in info.codeinfo[3]:
            codelines = open(info.codeinfo[0]).readlines()
            end = info.codeinfo[1]
            start = end
            while decorator_name not in codelines[start] and end - start <= 4:
                start -= 1
            info.codeinfo = info.codeinfo[:-1] + (''.join(codelines[start:end]),)

        if info.scope == 'class':  # pragma: no cover
            # if the decorator was attached to a method in a class, or
            # otherwise executed at class scope, we need to set an
            # 'attr' into the settings if one isn't already in there
            if settings.get('attr') is None:
                settings['attr'] = wrapped.__name__

        settings['_info'] = info.codeinfo  # fbo "action_method"
        return wrapped


class IterEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError, catched:
            if isinstance(obj, GeneratorType):
                return list(obj)
            if isinstance(obj, ResultsWrapper):
                return list(obj)
            elif isinstance(obj, datetime):
                return datetime_to_rfc3339(obj)
            raise catched


class JSONResourceRoot(object):
    """
    """
    response_content_type = 'application/json'

    def __init__(self, data, status_code=200, stats=False, remaining=False):
        """
        """
        self.data = data
        self.status_code = status_code
        self.stats = stats
        self.remaining = remaining
        self.headers = {}

    def __call__(self, *args, **kwargs):
        return self.buildResponse(*args, **kwargs)

    def buildResponse(self, payload=None):
        """
            Translate to JSON object if any data. If data is not a list
            something went wrong
        """
        if self.stats:
            response_payload = ''
            self.headers['X-totalItems'] = str(self.data)
        else:
            response_payload = json.dumps(self.data, cls=IterEncoder)

        if self.remaining:
            self.headers['X-Has-Remaining-Items'] = '1'

        data = response_payload is None and self.data or response_payload
        response = Response(data, status_int=self.status_code)
        response.content_type = self.response_content_type
        for key, value in self.headers.items():
            response.headers.add(key, value)
        return response


class JSONResourceEntity(object):
    """
    """
    response_content_type = 'application/json'

    def __init__(self, request, data, status_code=200):
        """
        """
        self.request = request
        self.data = data
        self.status_code = status_code

    def __call__(self, *args, **kwargs):
        return self.buildResponse(*args, **kwargs)

    def buildResponse(self, payload=None):
        """
            Translate to JSON object if any data. If data is not a dict,
            something went wrong
        """
        if 'show_acls' in self.request.params:
            self.data['acls'] = self.request.context.dump_acls()

        response_payload = json.dumps(self.data, cls=IterEncoder)
        data = response_payload is None and self.data or response_payload
        response = Response(data, status_int=self.status_code)
        response.content_type = self.response_content_type

        return response
