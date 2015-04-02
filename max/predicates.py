# -*- coding: utf-8 -*-
from max.exceptions import UnknownUserError


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
            raise UnknownUserError('Unknown actor identified by username: {}'.format(request.actor_username))

        return True
