Owner = 'Owner'
Manager = 'Manager'


def is_owner(context, userid):
    """
        Checks if a user owns a object.

        If the object has no ownership information, returns False.
    """
    try:
        return context['_owner'] == userid
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
    return security.get_user_roles(userid)
