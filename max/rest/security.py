# -*- coding: utf-8 -*-
from max import ALLOWED_ROLES
from max.exceptions import ObjectNotFound
from max.exceptions import ValidationError
from max.resources import loadMAXSecurity
from max.rest.ResourceHandlers import JSONResourceRoot
from max.rest.ResourceHandlers import JSONResourceEntity
from max.rest import endpoint
from max.security.permissions import manage_security
from pyramid.httpexceptions import HTTPNoContent


@endpoint(route_name='admin_security', request_method='GET', requires_actor=False, permission=manage_security)
def getSecurity(security, request):
    """
         /admin/security

         Expose the current MAX security roles and its members

         It's intended to be a protected by IP endpoint as we do not want
         eavesdroping on this information
    """
    handler = JSONResourceRoot(security.flatten())
    return handler.buildResponse()


@endpoint(route_name='admin_security_users', request_method='GET', requires_actor=False, permission=manage_security)
def getSecurityUsers(security, request):
    """
         /admin/security/users

         Expose the current MAX security roles and its members, grouped by  users

         It's intended to be a protected by IP endpoint as we do not want
         eavesdroping on this information
    """
    users = {}
    for role in ALLOWED_ROLES:
        for username in security['roles'].get(role, []):
            users.setdefault(username, {})
            users[username][role] = True

    user_roles = [{'username': username, 'roles': [{'name': role, 'active': user_roles.get(role, False)} for role in ALLOWED_ROLES]} for username, user_roles in users.items()]

    handler = JSONResourceRoot(user_roles)
    return handler.buildResponse()


@endpoint(route_name='admin_security_role_user', request_method='GET', requires_actor=False, permission=manage_security)
def check_user_role(security, request):
    """
    """

    role = request.matchdict['role']
    user = request.matchdict['user']

    security.setdefault('roles', {})
    security['roles'].setdefault(role, [])

    if role not in ALLOWED_ROLES:
        raise ValidationError('Role "{}" is not a valid role'.format(role))

    if user not in security['roles'][role]:
        raise ObjectNotFound("User {} doesn't have role {}".format(user, role))

    handler = JSONResourceEntity({'roles': [role]})
    return handler.buildResponse()


@endpoint(route_name='admin_security_role_user', request_method='POST', requires_actor=False, permission=manage_security)
def add_user_to_role(security, request):
    """
         /admin/security/roles/{role}/users/{user}

         Adds a user to a role
    """
    role = request.matchdict['role']
    user = request.matchdict['user']

    if role not in ALLOWED_ROLES:
        raise ValidationError('Role "{}" is not a valid role'.format(role))

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


@endpoint(route_name='admin_security_role_user', request_method='DELETE', requires_actor=False, permission=manage_security)
def remove_user_from_role(security, request):
    """
         /admin/security/roles/{role}/users/{user}

         Removes a user from a role
    """
    role = request.matchdict['role']
    user = request.matchdict['user']

    if role not in ALLOWED_ROLES:
        raise ValidationError('Role "{}" is not a valid role'.format(role))

    security.setdefault('roles', {})
    security['roles'].setdefault(role, [])
    if user not in security['roles'][role]:
        raise ObjectNotFound("User {} in not in {} role list".format(user, role))

    # Make sure we delete the user, even if it's declared more than onece
    while user in security['roles'][role]:
        security['roles'][role].remove(user)
    security.save()
    request.registry.max_security = loadMAXSecurity(request.registry)
    return HTTPNoContent()
