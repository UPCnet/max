# -*- coding: utf-8 -*-
from max import ALLOWED_ROLES
from max.exceptions import ObjectNotFound
from max.exceptions import ValidationError
from max.rest import JSONResourceEntity
from max.rest import JSONResourceRoot
from max.rest import endpoint
from max.security.permissions import manage_security

from pyramid.httpexceptions import HTTPNoContent


@endpoint(route_name='admin_security', request_method='GET', permission=manage_security)
def getSecurity(security, request):
    """
        Get security settings

        Expose the current MAX security roles and its members
    """
    handler = JSONResourceRoot(request, security.flatten())
    return handler.buildResponse()


@endpoint(route_name='admin_security_users', request_method='GET', permission=manage_security)
def getUsersRoles(security, request):
    """
        Get users roles
    """
    users = {}
    for role in ALLOWED_ROLES:
        for username in security['roles'].get(role, []):
            users.setdefault(username, {})
            users[username][role] = True

    user_roles = [{'username': username, 'roles': [{'name': role, 'active': user_roles.get(role, False)} for role in ALLOWED_ROLES]} for username, user_roles in users.items()]

    handler = JSONResourceRoot(request, user_roles)
    return handler.buildResponse()


@endpoint(route_name='admin_security_role_user', request_method='GET', permission=manage_security)
def check_user_role(security, request):
    """
        Check if user has a role
    """

    role = request.matchdict['role']
    user = request.matchdict['user']

    if role not in ALLOWED_ROLES:
        raise ValidationError('Role "{}" is not a valid role'.format(role))

    if not security.has_role(user, role):
        raise ObjectNotFound("User {} doesn't have role {}".format(user, role))

    handler = JSONResourceEntity(request, {'roles': [role]})
    return handler.buildResponse()


@endpoint(route_name='admin_security_role_user', request_method='POST', permission=manage_security)
def add_user_to_role(security, request):
    """
        Grants a role to a user
    """
    role = request.matchdict['role']
    user = request.matchdict['user']

    if role not in ALLOWED_ROLES:
        raise ValidationError('Role "{}" is not a valid role'.format(role))

    added = security.add_user_to_role(user, role)
    status_code = 201 if added else 200
    if added:
        security.save()
    handler = JSONResourceRoot(request, security.flatten()['roles'][role], status_code=status_code)
    return handler.buildResponse()


@endpoint(route_name='admin_security_role_user', request_method='DELETE', permission=manage_security)
def remove_user_from_role(security, request):
    """
        Removes a role from a user
    """
    role = request.matchdict['role']
    user = request.matchdict['user']

    if role not in ALLOWED_ROLES:
        raise ValidationError('Role "{}" is not a valid role'.format(role))

    if not security.has_role(user, role):
        raise ObjectNotFound("User {} doesn't have role {}".format(user, role))

    removed = security.remove_user_from_role(user, role)
    if removed:
        security.save()
    return HTTPNoContent()
