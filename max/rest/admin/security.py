# -*- coding: utf-8 -*-
from pyramid.view import view_config

from max import ALLOWED_ROLES
from max.exceptions import ObjectNotFound, ValidationError
from max.resources import loadMAXSecurity
from max.decorators import MaxResponse
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot


@view_config(route_name='admin_security', request_method='GET')
@MaxResponse
def getSecurity(context, request):
    """
         /admin/security

         Expose the current MAX security roles and its members

         It's intended to be a protected by IP endpoint as we do not want
         eavesdroping on this information
    """
    mmdb = MADMaxDB(context.db)
    query = {}
    roles = mmdb.security.search(query, flatten=1)

    handler = JSONResourceRoot(roles)
    return handler.buildResponse()


@view_config(route_name='admin_security_role_user', request_method='POST', restricted="Manager")
@MaxResponse
def add_user_to_role(context, request):
    """
         /admin/security/roles/{role}/users/{user}

         Adds a user to a role
    """
    role = request.matchdict['role']
    user = request.matchdict['user']

    if role not in ALLOWED_ROLES:
        raise ValidationError('Role "{}" is not a valid role'.format(role))

    mmdb = MADMaxDB(context.db)
    query = {}
    security = mmdb.security.search(query)[0]
    security.setdefault('roles', {})
    security['roles'].setdefault(role, [])
    status_code = 200
    if user not in security['roles'][role]:
        security['roles'][role].append(user)
        status_code = 201
    # Remove possible duplicates from list
    security['roles'][role] = list(set(security['roles'][role]))
    security.save()
    request.registry.max_security = loadMAXSecurity(request.registry)
    handler = JSONResourceRoot(security.flatten()['roles'][role], status_code=status_code)
    return handler.buildResponse()


@view_config(route_name='admin_security_role_user', request_method='DELETE', restricted="Manager")
@MaxResponse
def remove_user_from_role(context, request):
    """
         /admin/security/roles/{role}/users/{user}

         Removes a user from a role
    """
    role = request.matchdict['role']
    user = request.matchdict['user']

    if role not in ALLOWED_ROLES:
        raise ValidationError('Role "{}" is not a valid role'.format(role))

    mmdb = MADMaxDB(context.db)
    query = {}
    security = mmdb.security.search(query)[0]
    security.setdefault('roles', {})
    security['roles'].setdefault(role, [])
    if user not in security['roles'][role]:
        raise ObjectNotFound("User {} in not in {} role list".format(user, role))

    # Make sure we delete the user, even if it's declared more than onece
    while user in security['roles'][role]:
        security['roles'][role].remove(user)
    security.save()
    request.registry.max_security = loadMAXSecurity(request.registry)
    handler = JSONResourceRoot(security.flatten()['roles'][role], status_code=200)
    return handler.buildResponse()
