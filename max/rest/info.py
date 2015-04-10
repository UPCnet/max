# -*- coding: utf-8 -*-
from max import RESOURCES
from max.resources import Root
from max.rest import JSONResourceEntity
from max.security.permissions import view_server_settings

from pyramid.response import Response
from pyramid.view import view_config

import json
import pkg_resources
import re
import sys


@view_config(context=Root)
def rootView(context, request):

    message = 'I am a max server'
    response = Response(message)
    return response


@view_config(route_name='info', request_method='GET')
def getMaxPublicInfo(context, request):
    """
        /info

        Returns max server settings, only the ones allowed unauthenticad
    """
    allowed_settings = [
        'max.oauth_server',
        'max.stomp_server',
        'max.server_id'
    ]

    max_settings = request.registry.settings
    settings = {}
    for setting in allowed_settings:
        if setting in max_settings:
            settings[setting] = max_settings[setting]

    settings['version'] = pkg_resources.require("max")[0].version
    handler = JSONResourceEntity(settings)
    return handler.buildResponse()


@view_config(route_name='info_settings', request_method='GET', permission=view_server_settings)
def getMaxSettings(context, request):
    """
        /info/settings

        Returns all max server settings
    """
    max_settings = request.registry.settings
    settings = {key: value for key, value in max_settings.items() if re.match('^(max|mongodb|cache|oauth)', key)}
    settings['version'] = pkg_resources.require("max")[0].version

    handler = JSONResourceEntity(settings)
    return handler.buildResponse()


@view_config(route_name='info_api', request_method='GET')
def endpoints_view(context, request):
    """
    """
    views = request.registry.introspector.get_category('views')

    def max_views():
        """
            Return route and view instrospection information
            for all endpoints defined on RESOURCES (except this view)
        """
        for view in views:
            related = view.get('related')
            if related:
                route = related[0].get('object', None)
                if route is not None:
                    if route.name in RESOURCES and \
                       route.name != 'info_api' and \
                       view['introspectable'].action_info.src.startswith('@endpoint'):
                            yield view, route

    def view_permission(view):
        for item in view['related']:
            if item.category_name == 'permissions':
                return item.discriminator
        return 'Anonymous'

    def get_query_params(method):
        params = []
        endpoint_query_params = re.findall(r':query(\*?)\s+({.*?})\s+(.*?)\n', method.__doc__, re.MULTILINE)
        for required, data, description in endpoint_query_params:
            params.append({
                'required': required == '*',
                'data': json.loads(data),
                'description': description
            })
        return params

    def get_rest_params(method):
        params = []
        endpoint_rest_params = re.findall(r':rest\s+([\w\d\_\-]+)\s+(.*?)\n', method.__doc__, re.MULTILINE)
        for name, description in endpoint_rest_params:
            params.append({
                'name': name,
                'description': description
            })
        return params

    resources_by_route = {}

    # Group all views by route and request method
    for view, route in max_views():
        view_settings = view['introspectable']
        resource_info = {
            'route': route.pattern,
            'id': route.name,
            'name': RESOURCES[route.name].get('name', route.name),
            'filesystem': RESOURCES[route.name].get('filesystem', False),
            'url': RESOURCES[route.name].get('route'),
            'category': RESOURCES[route.name].get('category', 'Uncategorized'),
            'methods': {},
        }

        # Import the method implementing the endpoint to get the docstring
        module_fqdn = re.search(r'(?:max|\.egg)/(max/.*)\.py$', view_settings.action_info.file).groups()[0].replace('/', '.')
        module_namespace, module_name = re.search(r'(.*?)\.([^\.]+$)', module_fqdn).groups()

        method_name = re.search(r'([^.]+)$', view_settings.title).groups()[0]
        module = getattr(sys.modules[module_namespace], module_name)
        method = getattr(sys.modules[module_fqdn], method_name)

        is_head = False
        if view_settings['request_methods'] == 'GET':
            code = open(module.__file__.rstrip('c')).read()
            method_code = re.search(r'def\s+{}(.*?)(?:\n@|$)'.format(method_name), code, re.DOTALL)
            is_head = re.search(r"request\.method\s+==\s+'HEAD'", method_code.groups()[0])

        resources_by_route.setdefault(route.name, resource_info)

        endpoint_description_match = re.match(r'^\s*(.*?)\n\s*(\n|$)', method.__doc__, re.MULTILINE)
        # if not endpoint_description_match:
        #     import ipdb;ipdb.set_trace()
        endpoint_description = endpoint_description_match.groups()[0]
        endpoint_documentation = method.__doc__[endpoint_description_match.end():].strip()

        method_info = {
            'description': endpoint_description,
            'documentation': endpoint_documentation if endpoint_documentation else 'Please document me!',
            'rest_params': get_rest_params(method),
            'query_params': get_query_params(method),
            'permission': view_permission(view)
        }

        # In case we found that the GET method has a HEAD version
        # append HEAD in order to duplicate method info entry of GET as HEAD
        methods = [view_settings['request_methods']]
        if view_settings['request_methods'] == 'GET' and is_head:
            methods.append('HEAD')

        for req_method in methods:
            # Create method entry
            resources_by_route[route.name]['methods'][req_method] = method_info

    if request.params.get('by_category'):
        endpoints = resources_by_route
        endpoints_by_category = {}

        for route_name, route_info in endpoints.items():
            endpoints_by_category.setdefault(route_info['category'], [])
            endpoints_by_category[route_info['category']].append(route_info)

        sorted_categories = endpoints_by_category.keys()
        sorted_categories.sort()

        categories = []
        for category_name in sorted_categories:

            routes = []
            for route_info in endpoints_by_category[category_name]:
                routes.append({
                    'route_id': route_info['id'],
                    'filesystem': route_info['filesystem'],
                    'route_name': route_info['name'],
                    'route_url': route_info['url'],
                    'methods': route_info['methods']
                })
            category = {
                'name': category_name,
                'id': category_name.lower().replace(' ', '-'),
                'resources': sorted(routes, key=lambda route: route['route_name'])
            }
            categories.append(category)

        handler = JSONResourceEntity(categories)
    else:
        handler = JSONResourceEntity(resources_by_route)

    return handler.buildResponse()
