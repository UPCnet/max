from copy import copy

import operator


from max.rest.utils import getUrlHashFromURI
from max.rest.utils import getUsernameFromPOSTBody
from max.rest.utils import getUsernameFromURI
from max.rest.utils import getUsernameFromXOAuth
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


class RequiredUserPredicate(object):
    def __init__(self, required, config):
        self.required = required
        self.registry = config.registry

    def text(self):
        return 'User must exist' if self.required else 'User may not exist'

    phash = text

    def __call__(self, context, request):

        oauth_username = getUsernameFromXOAuth(request)
        username = str(oauth_username)  # To avoid variable reference

        # If we have a username in the URI, take it
        uri_username = getUsernameFromURI(request)
        if uri_username:
            username = uri_username.lower()

        target_user = getUsernameFromPOSTBody(request)

        # Check a valid actor exists in the database
        if self.required:
            try:
                actor = getUserActor(self.registry.max_store, username)
            except IndexError:
                raise UnknownUserError('Unknown actor identified by username: %s' % username)

        def getActor(request):
            try:
                actor.setdefault('displayName', actor['username'])
                return actor
            except:
                return None

        request.set_property(getActor, name='actor', reify=True)

        # Inner methods define here to use var username as a closure

        def getTarget(request):
            return target_user

        def getCreator(request):
            return username

        def getRoles(request):
            security = request.registry.max_security
            user_roles = [role for role, users in security.get("roles", {}).items() if username in users]
            return user_roles + ['Authenticated']

        request.set_property(getCreator, name='creator', reify=True)
        request.set_property(getRoles, name='roles', reify=True)
        request.set_property(getTarget, name='target_user', reify=True)

        return True
