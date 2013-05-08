import sys
import os
import re
from prettytable import PrettyTable, ALL
from sh import git


TEMPLATE = """

Estat dels webservices
======================

{}

"""

TABLE_TEMPLATE = """

{}
{}

{}

"""


def addMissingCodeErrors(container, resources, name, prefix=''):
    """
        Found docs or tests for missing implementation WTF
    """
    res = resources[name]
    for method in ['GET', 'POST', 'PUT', 'DELETE']:
        has_docs = res.get(prefix + 'documentation', {}).get(method, False)
        has_test = method in res.get(prefix + 'tests', [])
        has_code = res.get(prefix + 'methods', {}).get(method, False)
        if (has_docs or has_test) and not has_code:
            container.append('  ERROR: {} {} is documented or tested but code not found by parser'.format(method, res['route']))


def addUntestedCodeErrors(container, resources, name, prefix=''):
    """
        Has code but no tests found
    """
    found = []
    res = resources[name]
    for method in ['GET', 'POST', 'PUT', 'DELETE']:
        has_test = method in res.get(prefix + 'tests', [])
        has_code = res.get(prefix + 'methods', {}).get(method, False)
        if has_code and not has_test:
            found.append(method)
    if found:
        container.append('  {} ({})'.format(res['route'], ', '.join(found)))


def addUndocumentedCodeErrors(container, resources, name, prefix=''):
    """
        Has code but no docs found
    """
    found = []
    res = resources[name]
    for method in ['GET', 'POST', 'PUT', 'DELETE']:
        has_docs = res.get(prefix + 'documentation', {}).get(method, False)
        has_code = res.get(prefix + 'methods', {}).get(method, False)
        if has_code and not has_docs:
            found.append(method)
    if found:
        container.append('  {} ({})'.format(res['route'], ', '.join(found)))


def getFunctionLineNumbers(code, func_code, fname):
    start = code[:code.find(func_code)].count('\n') + 1
    end = start + func_code.count('\n')
    return start, end


def getEndpointStatus(resources, name, method, prefix=''):
    status = ''
    if method in resources[name].get(prefix + 'methods', {}):
        method_d = resources[name].get(prefix + 'methods')[method]
        status += '.. hint:: `CODE <{url}#L{startline}-L{endline}>`_'.format(**method_d)
    if method in resources[name].get(prefix + 'documentation', []):
        method_d = resources[name].get(prefix + 'documentation')[method]
        status += '\n.. tip:: `DOCS <{url}>`_'.format(**method_d)
    if method in resources[name].get(prefix + 'tests', []):
        status += '\n.. attention:: TEST'

    return status


def main(argv=sys.argv):
    print
    import max.rest

    # Get declared routes
    from max.rest.resources import RESOURCES
    resources = dict(RESOURCES)

    restricted_routes_with_code = []
    tables = ''
    errors = []
    untested = []
    undocumented = []

    total_functions = 0
    # Walk trough code looking for view declarations
    # and collect which methods are implemented for each route
    gitdir = git.bake('--git-dir', '{}/.git'.format(re.sub(r'(.*?)/max$', r'\1', max.__path__[0])))
    commit_id = re.search(r'([\dabcdef]{40})', gitdir('log', n=1, pretty='oneline').stdout).group()
    github_base_url = 'https://github.com/UPCnet/max/tree/{}'.format(commit_id)
    maxpath = max.rest.__path__[0]
    paths = [maxpath, '%s/admin' % maxpath]
    for path in paths:
        for item in os.listdir(path):
            filename = '%s/%s' % (path, item)
            if os.path.isfile(filename):
                if filename.endswith('.py'):
                    code = open(filename).read()
                    function_lines = re.findall(r'\n\s*@view_config\((.*?)\).*?def\s+([^\(]+)(.*?)(?=\n+(?:[^\s]|$)+)', code, re.DOTALL)
                    if function_lines:
                        for fun in function_lines:
                            function_params, function_name, function_code = fun
                            params = dict(re.findall(r'([\w_]+)=[\'"]([\w_]+)[\'"]', function_params))
                            if not 'HTTPNotImplemented' in function_code:
                                total_functions += 1
                                try:
                                    method = params['request_method'].upper()
                                    code_key = 'methods'
                                    if 'restricted' in params.keys() or resources[params['route_name']]['route'].startswith('/admin'):
                                        code_key = 'restricted_' + code_key
                                        restricted_routes_with_code.append(params['route_name'])

                                    resources[params['route_name']].setdefault(code_key, {})
                                    startline, endline = getFunctionLineNumbers(code, function_code, function_name)
                                    resources[params['route_name']][code_key][method] = {
                                        'url': '{}/{}'.format(github_base_url, filename.split('src/max/')[-1]),
                                        'startline': startline,
                                        'endline': endline}
                                except:
                                    pass

    print ' > Found {} active view definitions'.format(total_functions)

    # Walk through documentation looking for enpoint headers:
    maxdocspath = '/'.join(maxpath.split('/')[:-2]) + '/docs/ca'
    docs = [('apirest', 'documentation'), ('apioperations', 'restricted_documentation')]

    base_url = 'file:///var/pyramid/maxdevel/src/max/docs/_build/html/ca'
    base_url = '/docs/v3/ca'
    total_docs = 0
    for doc, dockey in docs:
        docpath = '{}/{}.rst'.format(maxdocspath, doc)
        text = open(docpath).read()
        documented = re.findall(r'\.\. http:(\w+):: (.*?)\n', text)
        for method, route in documented:
            match_route = [name for name, rroute in resources.items() if re.sub(r'{(\w+)}', r':', rroute['route']) == re.sub(r'{(\w+)}', ':', route)]

            if match_route:
                total_docs += 1
                resources[match_route[0]].setdefault(dockey, {})
                anchor = '{}-{}'.format(method.lower(), re.sub(r'\/', r'-', route))
                resources[match_route[0]][dockey][method.upper()] = {
                    'url': '{}/{}.html#{}'.format(base_url, doc, anchor)}
            else:
                errors.append('ERROR: Route not matched for documented method {} {}, in file {}'.format(method.upper(), route, filename))

    print ' > Found {} method documentation entries'.format(total_docs)

    # Walk trough tests looking for endpoint routes:
    maxtestspath = '/'.join(maxpath.split('/')[:-2]) + '/max/tests'
    for filename in os.listdir(maxtestspath):
        if filename.startswith('test_'):
            testpath = '{}/{}'.format(maxtestspath, filename)
            text = open(testpath).read()
            tested = re.findall(r'(get|post|put|delete)\([\"\'](\/+.*?)[\?\"\'].*?oauth2Header\((.*?)\)', text, re.IGNORECASE)
            for method, route, user in tested:
                route = re.sub(r'/{2,}', r'/', route)
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
                else:
                    errors.append('ERROR: Route not matched when using {} {}, in file {}'.format(method.upper(), route, filename))

#    restricted_docs = ['apioperations.rst']

    sections = [
        ('Usuaris Normals', ''),
        ('Usuaris Restringits', 'restricted_')
    ]

    routes = [(name, re.sub(r'{(\w+)}', r':\1', route['route'])) for name, route in resources.items()]
    sorted_routes = sorted(routes, key=lambda x: x[1])

    for title, prefix in sections:

        table1 = PrettyTable(['Endpoint', '**GET**', '**POST**', '**PUT**', '**DELETE**'])
        table1.hrules = ALL
        table1.align['Endpoint'] = "l"
        table1.align['**GET**'] = "l"
        table1.align['**POST**'] = "l"
        table1.align['**PUT**'] = "l"
        table1.align['**DELETE**'] = "l"

        for name, route in sorted_routes:
            row = ['``{}``'.format(route),
                   getEndpointStatus(resources, name, 'GET', prefix=prefix),
                   getEndpointStatus(resources, name, 'POST', prefix=prefix),
                   getEndpointStatus(resources, name, 'PUT', prefix=prefix),
                   getEndpointStatus(resources, name, 'DELETE', prefix=prefix),
                   ]
            addMissingCodeErrors(errors, resources, name, prefix=prefix)
            addUntestedCodeErrors(untested, resources, name, prefix=prefix)
            addUndocumentedCodeErrors(undocumented, resources, name, prefix=prefix)

            table1.add_row(row)
        tables += TABLE_TEMPLATE.format(title, '-' * len(title), table1.get_string())

    open('{}/report.rst'.format(maxdocspath), 'w').write(TEMPLATE.format(tables))
    print ' > Generated new {}'.format('{}/report.rst'.format(maxdocspath))
    print
    if errors:
        print 'Errors'
        print '======'
        print
        print '\n'.join(errors)
        print
    if undocumented:
        print 'Undocumented Code'
        print '================='
        print
        print '\n'.join(undocumented)
        print
    if untested:
        print 'Untested Code'
        print '============='
        print
        print '\n'.join(untested)
        print
    print
