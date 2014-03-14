from pyramid.view import view_config
from max.rest.resources import RESOURCES
from max.rest.ResourceHandlers import JSONResourceEntity
from max.predicates import RestrictedPredicate
import re
import sys
import json


@view_config(route_name='endpoints', request_method='GET')
def endpoints(context, request):
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
                    if route.name in RESOURCES and route.name != 'endpoints':
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
            'category': RESOURCES[route.name].get('category', 'Uncategorized'),
            'methods': {},
        }

        # Import the method implementing the endpoint to get the docstring
        module_name = re.search(r'max/(max/.*)\.py$', view.action_info.file).groups()[0].replace('/', '.')
        method_name = view.action_info.src
        method = getattr(sys.modules[module_name], method_name)

        resources_by_route.setdefault(route.name, resource_info)
        endpoint_description = re.match(r'^\s*(.*?)\s*(?:$|:query)', method.__doc__, re.MULTILINE).groups()[0]

        roles = restricted_roles(view)

        method_info = {
            'description': endpoint_description,
            'rest_params': get_rest_params(method),
            'query_params': get_query_params(method)
        }

        # Create method entry
        resources_by_route[route.name]['methods'].setdefault(view['request_methods'], {})

        for role in roles:
            resources_by_route[route.name]['methods'][view['request_methods']][role] = method_info

    handler = JSONResourceEntity(resources_by_route)
    return handler.buildResponse()
