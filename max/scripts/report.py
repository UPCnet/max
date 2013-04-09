import sys
import os
import re
from prettytable import PrettyTable, ALL


TEMPLATE = """

Estat dels webservices
======================

Usuaris normals
---------------

{}

Usuaris restringits
---------------

{}



"""


def getEndpointStatus(resources, name, method, prefix=''):
    status = ''
    if method in resources[name].get(prefix + 'methods', []):
        status += '.. hint:: CODE'
    if method in resources[name].get(prefix + 'documentation', []):
        status += '\n.. tip:: DOCS'
    if method in resources[name].get(prefix + 'tests', []):
        status += '\n.. attention:: TEST'

    return status


def main(argv=sys.argv):
    import max.rest

    # Get declared routes
    from max.rest.resources import RESOURCES
    resources = dict(RESOURCES)

    restricted_routes_with_code = []

    # Walk trough code looking for view declarations
    # and collect which methods are implemented for each route
    maxpath = max.rest.__path__[0]
    paths = [maxpath, '%s/admin' % maxpath]
    for path in paths:
        for item in os.listdir(path):
            filename = '%s/%s' % (path, item)
            if os.path.isfile(filename):
                if filename.endswith('.py'):
                    code = open(filename).read()
                    function_lines = re.findall(r'@view_config\((.*?)\)', code)
                    if function_lines:
                        functions_params = [dict(re.findall(r'([\w_]+)=[\'"]([\w_]+)[\'"]', a)) for a in function_lines]
                        for fun in functions_params:
                            try:
                                resources[fun['route_name']].setdefault('methods', [])
                                resources[fun['route_name']].setdefault('restricted_methods', [])
                                method = fun['request_method']
                                if 'restricted' in fun.keys():
                                    restricted_routes_with_code.append(fun['route_name'])
                                    resources[fun['route_name']]['restricted_methods'].append(method)
                                else:
                                    resources[fun['route_name']]['methods'].append(method)
                            except:
                                pass

    # Walk through documentation looking for enpoint headers:
    maxdocspath = '/'.join(maxpath.split('/')[:-2]) + '/docs/ca'
    docs = [('apirest.rst', 'documentation'), ('apioperations.rst', 'restricted_documentation')]

    for doc, dockey in docs:
        docpath = '{}/{}'.format(maxdocspath, doc)
        text = open(docpath).read()
        documented = re.findall(r'\.\. http:(\w+):: (.*?)\n', text)
        for method, route in documented:
            match_route = [name for name, rroute in resources.items() if re.sub(r'{(\w+)}', r':', rroute['route']) == re.sub(r'{(\w+)}', ':', route)]

            if match_route:
                resources[match_route[0]].setdefault(dockey, [])
                resources[match_route[0]][dockey].append(method.upper())
            # else:
            #     print method, route

    # Walk trough tests looking for endpoint routes:
    maxtestspath = '/'.join(maxpath.split('/')[:-2]) + '/max/tests'
    for filename in os.listdir(maxtestspath):
        if filename.startswith('test_'):
            testpath = '{}/{}'.format(maxtestspath, filename)
            text = open(testpath).read()
            tested = re.findall(r'(get|post|put|delete)\([\"\'](\/.*?)[\?\"\'].*?oauth2Header\((.*?)\)', text, re.IGNORECASE)
            for method, route, user in tested:
                match_route = [name for name, rroute in resources.items() if re.sub(r'{(\w+)}', r':', rroute['route']) == re.sub(r'{(\w*)}|%s', r':', route)]
                if match_route:
                    if 'test_manager' in user and match_route[0] in restricted_routes_with_code:
                        resources[match_route[0]].setdefault('restricted_tests', [])
                        resources[match_route[0]]['restricted_tests'].append(method.upper())
                    else:
                        if 'test_manager' in user:
                            print 'mismatched user'
                        resources[match_route[0]].setdefault('tests', [])
                        resources[match_route[0]]['tests'].append(method.upper())
                # else:
                #     print method, route, user

#    restricted_docs = ['apioperations.rst']

    table1 = PrettyTable(['Endpoint', '**GET**', '**POST**', '**PUT**', '**DELETE**'])
    table1.hrules = ALL
    table1.align['Endpoint'] = "l"
    table1.align['**GET**'] = "l"
    table1.align['**POST**'] = "l"
    table1.align['**PUT**'] = "l"
    table1.align['**DELETE**'] = "l"

    routes = [(name, re.sub(r'{(\w+)}', r':\1', route['route'])) for name, route in resources.items()]
    sorted_routes = sorted(routes, key=lambda x: x[1])

    for name, route in sorted_routes:
        row = ['``{}``'.format(route),
               getEndpointStatus(resources, name, 'GET'),
               getEndpointStatus(resources, name, 'POST'),
               getEndpointStatus(resources, name, 'PUT'),
               getEndpointStatus(resources, name, 'DELETE'),
               ]
        table1.add_row(row)

    table2 = PrettyTable(['Endpoint', '**GET**', '**POST**', '**PUT**', '**DELETE**'])
    table2.hrules = ALL
    table2.align['Endpoint'] = "l"
    table2.align['**GET**'] = "l"
    table2.align['**POST**'] = "l"
    table2.align['**PUT**'] = "l"
    table2.align['**DELETE**'] = "l"

    routes = [(name, re.sub(r'{(\w+)}', r':\1', route['route'])) for name, route in resources.items()]
    sorted_routes = sorted(routes, key=lambda x: x[1])

    for name, route in sorted_routes:
        row = ['``{}``'.format(route),
               getEndpointStatus(resources, name, 'GET', prefix='restricted_'),
               getEndpointStatus(resources, name, 'POST', prefix='restricted_'),
               getEndpointStatus(resources, name, 'PUT', prefix='restricted_'),
               getEndpointStatus(resources, name, 'DELETE', prefix='restricted_'),
               ]
        table2.add_row(row)

    open('{}/report.rst'.format(maxdocspath), 'w').write(TEMPLATE.format(table1.get_string(), table2.get_string()))

