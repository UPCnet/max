Owner = 'max.Owner'
Manager = 'Manager'


def is_owner(context, userid):
    """
        Checks if a user owns a object.

        If the object has no ownership information, returns False.
    """
    return getattr(context, '_owner', None) == userid


def get_user_roles(request, userid):
    """
        Returns the global max roles that userid posesses.
    """

    security = request.registry.max_security
    user_roles = [role for role, users in security.get("roles", {}).items() if userid in users]
    return user_roles
