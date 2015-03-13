# -*- coding: utf-8 -*-
from max.predicates import RestrictedPredicate
from max.rest.ResourceHandlers import JSONResourceEntity
from max.rest.resources import RESOURCES

from pyramid.view import view_config

import json
import re
import sys


@view_config(route_name='info_api', request_method='GET')
def endpoints_view(request):
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
                    if route.name in RESOURCES and route.name != 'info_api':
                        view_settings = view['introspectable']
                        yield view_settings, route

    def restricted_roles(view):
        for predicate in view['predicates']:
            if isinstance(predicate, RestrictedPredicate):
                roles = predicate.val if isinstance(predicate.val, list) else [predicate.val]
                return roles
        return ['Everyone']

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
        module_fqdn = re.search(r'(?:max|\.egg)/(max/.*)\.py$', view.action_info.file).groups()[0].replace('/', '.')
        module_namespace, module_name = re.search(r'(.*?)\.([^\.]+$)', module_fqdn).groups()
        method_name = view.action_info.src
        method = getattr(sys.modules[module_fqdn], method_name)
        module = getattr(sys.modules[module_namespace], module_name)

        is_head = False
        if view['request_methods'] == 'GET':
            code = open(module.__file__.rstrip('c')).read()
            method_code = re.search(r'def\s+{}(.*?)(?:\n@|$)'.format(method_name), code, re.DOTALL)
            if method_code:
                is_head = re.search(r"request\.method\s+==\s+'HEAD'", method_code.groups()[0])

        resources_by_route.setdefault(route.name, resource_info)
        endpoint_description = re.match(r'^\s*(.*?)\s*(?:$|:query)', method.__doc__, re.MULTILINE).groups()[0]

        roles = restricted_roles(view)

        method_info = {
            'description': endpoint_description,
            'rest_params': get_rest_params(method),
            'query_params': get_query_params(method)
        }

        # In case we found that the GET method has a HEAD version
        # append HEAD in order to duplicate method info entry of GET as HEAD
        methods = [view['request_methods']]
        if view['request_methods'] == 'GET' and is_head:
            methods.append('HEAD')

        for req_method in methods:
            # Create method entry
            resources_by_route[route.name]['methods'].setdefault(req_method, {})
            for role in roles:
                resources_by_route[route.name]['methods'][req_method][role] = method_info

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
