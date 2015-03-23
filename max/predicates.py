from copy import copy

import operator

from max.MADMax import MADMaxDB
from max.exceptions import UnknownUserError


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


def getUserActor(db, username):
    mmdb = MADMaxDB(db)
    actor = mmdb.users.getItemsByusername(username)[0]
    return actor


def getContextActor(db, hash):
    mmdb = MADMaxDB(db)
    context = mmdb.contexts.getItemsByhash(hash)[0]
    return context


class RequiredActorPredicate(object):
    def __init__(self, required, config):
        self.required = required
        self.registry = config.registry

    def text(self):
        return 'Actor is required to exist in the database' if self.required else 'Actor is not required to exists in the databse'

    phash = text

    def __call__(self, context, request):

        # Extraction of headers will raise exception here if headers missing
        # We want this to happen here, to raise Unauthorized before any hipotetical
        # other exception would raise (basically that the user in auth headers doesn't exists)
        oauth_token, username, scope = request.auth_headers

        if request.actor is None and self.required:
            raise UnknownUserError('Actor identified by: {} not found on database'.format(request.actor_username))

        return True
