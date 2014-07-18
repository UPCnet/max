from copy import copy

import operator


class RestrictedPredicate(object):
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'Restricted permissions to = %s' % (self.val,)

    phash = text

    def __call__(self, context, request):
        # Extract the username and token from request headers
        username = request.headers.get('X-Oauth-Username', '')
        allowed_roles = copy(self.val)
        if not isinstance(self.val, list):
            allowed_roles = [self.val, ]
        security = request.registry.max_security
        user_has_roles = [username in security.get("roles").get(role) for role in allowed_roles]
        user_is_allowed = reduce(operator.and_, user_has_roles, True)

        return user_is_allowed
