from copy import copy

import operator


class RestrictedPredicate(object):
    def __init__(self, val, config):
        self.val = val
        self.registry = config.registry

    def text(self):
        return 'Restricted permissions to = %s' % (self.val,)

    phash = text

    def __call__(self, context, request):
        # Extract the username and token from request headers
        username = request.headers.get('X-Oauth-Username', '')
        allowed_roles = copy(self.val)
        if not isinstance(self.val, list):
            allowed_roles = [self.val, ]
        security = self.registry.max_security
        user_has_roles = [username in security.get("roles").get(role) for role in allowed_roles]
        user_is_allowed = reduce(operator.and_, user_has_roles, True)
        method_is_head = request.method.upper() == 'HEAD'
        return user_is_allowed or method_is_head
