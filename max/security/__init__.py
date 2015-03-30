Owner = 'Owner'
Manager = 'Manager'


def is_manager(request, userid):
    """
        Returns whether the current authenticated user has the Manager role.
    """
    return Manager in get_user_roles(request, userid)


def is_owner(context, userid):
    """
        Checks if a user owns a object.

        If the object has no ownership information, returns False.
    """
    try:
        return getattr(context, '_owner') == userid
    except:
        return False


def is_self_operation(request):
    """
        Checks if the authenticated user is performing the action on himself

    """
    return request.authenticated_userid == request.actor_username


def get_user_roles(request, userid):
    """
        Returns the global max roles that userid posesses.
    """

    security = request.registry.max_security
    user_roles = [role for role, users in security.get("roles", {}).items() if userid in users]
    return user_roles
