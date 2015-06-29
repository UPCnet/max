# -*- coding: utf-8 -*-
from max.MADObjects import MADBase
from max.security import Manager
from max.security.permissions import manage_security

from pyramid.decorator import reify
from pyramid.security import Allow


class Security(MADBase):
    """
        The Security object representation
    """
    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, manage_security)
        ]
        return acl

    default_field_view_permission = manage_security
    default_field_edit_permission = manage_security
    collection = 'security'
    unique = '_id'
    schema = {
        '_id': {},
        'roles': {}
    }

    def _ensure_security(self):
        self.setdefault('roles', {})

    def add_user_to_role(self, user, role):
        """
            Grants a role to an user.

            Returns False if the user already had the role, True otherwise.
        """
        self._ensure_security()
        self['roles'].setdefault(role, [])

        # Remove possible duplicates from list
        self['roles'][role] = list(set(self['roles'][role]))

        if user not in self['roles'][role]:
            self['roles'][role].append(user)
            return True

        return False

    def remove_user_from_role(self, user, role):
        """
            Revokes a role from an user.

            Returns False if the user didn't had that role, True otherwise.
        """
        self._ensure_security()
        self['roles'].setdefault(role, [])

        # Remove possible duplicates from list
        self['roles'][role] = list(set(self['roles'][role]))

        if user in self['roles'][role]:
            self['roles'][role].remove(user)
            return True

        return False

    def get_role_users(self, role):
        """
            Get a list of all users that have a particular role.
        """
        self._ensure_security()
        return self['roles'].get(role, [])

    def get_user_roles(self, user):
        """
            Get a list of all the roles that a user has.
        """
        self._ensure_security()
        return [role for role, users in self["roles"].items() if user in users]

    def has_role(self, user, role):
        """
            Check if an user has a particular role
        """
        self._ensure_security()
        return user in self.get_role_users(role)
