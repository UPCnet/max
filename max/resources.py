# -*- coding: utf-8 -*-
from max import maxlogger
from max.MADMax import MADMaxCollection
from pyramid.security import Allow, Authenticated

from max.security import Manager, is_self_operation, Owner
from max.security import permissions

import pkg_resources
import inspect


DUMMY_CLOUD_API_DATA = {
    "twitter": {
        "consumer_secret": "",
        "access_token": "",
        "consumer_key": "",
        "access_token_secret": ""
    }
}


def get_pyramid_authorization_frame():
    """
        Returns the upper frame if we determine that on this point,
        pyramid is checking the acls from the permits  method of the
        authorization module
    """

    frame = inspect.currentframe().f_back.f_back
    parent_method = frame.f_code.co_name
    parent_filename = frame.f_code.co_filename
    if parent_method == 'permits' and parent_filename.endswith('pyramid/authorization.py'):
        return frame


class Root(dict):
    __parent__ = __name__ = None

    @property
    def __acl__(self):
        acl = [
        ]

        # Grant the permission associated with the view to the authenticated user
        # ONLY when we're making a HEAD request. This way we can keep view permissions sane
        # Related to GET methods, while allowing HEAD counterpart available to the
        # requesting user
        if self.request.method == 'HEAD':
            frame = get_pyramid_authorization_frame()
            if frame:
                required_view_permission = frame.f_locals['permission']
                acl.append((Allow, self.request.authenticated_userid, required_view_permission))

        return acl

    def __init__(self, request):
        self.request = request
        # MongoDB:
        registry = self.request.registry
        self.db = registry.max_store
        self['contexts'] = ContextTraverser(self, request)
        self['people'] = PeopleTraverser(self, request)
        self['subscriptions'] = SubscriptionsTraverser(self, request)


class MongoDBTraverser(MADMaxCollection):

    collection_name = ''
    query_key = '_id'

    def __init__(self, parent, request):
        self.request = request
        self.__parent__ = parent
        self.collection = self.request.registry.max_store[self.collection_name]
        self.show_fields = None


class ContextTraverser(MongoDBTraverser):
    collection_name = 'contexts'
    query_key = 'hash'

    @property
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.add_context),
            (Allow, Manager, permissions.list_contexts),
            (Allow, Authenticated, permissions.list_public_contexts),
            (Allow, Manager, permissions.modify_context),
            (Allow, Manager, permissions.delete_context),
            (Allow, Manager, permissions.view_context),
            (Allow, Manager, permissions.view_context_activity)
        ]
        return acl


class PeopleTraverser(MongoDBTraverser):
    collection_name = 'users'
    query_key = 'username'

    @property
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.add_people),
            (Allow, Manager, permissions.list_all_people),
            (Allow, Manager, permissions.modify_user),
            (Allow, Manager, permissions.delete_user),
            (Allow, Authenticated, permissions.list_visible_people),
            (Allow, Authenticated, permissions.view_user_profile),
        ]

        # Grant add permission if user is trying to create itself
        if self.request.authenticated_userid == self.request.actor_username:
            acl.append((Allow, self.request.authenticated_userid, permissions.add_people))

        return acl


class Subscription(object):
    def __init__(self, parent, request, chash, actor):
        from max.models import Context
        self.__parent__ = parent
        self.request = request
        self.hash = chash
        self.actor = actor
        self.context = Context()
        self.context.fromObject({'objectType': 'context', 'hash': chash})
        self.subscription = actor.getSubscription({'hash': chash, 'objectType': 'context'})

    @property
    def _owner(self):
        """
            Proxy of the ownership of the underliying context
        """
        return self.context._owner

    def __acl__(self):
        acl = []

        # Grant ubsubscribe permission if the user subscription allows it
        # but only if is trying to unsubscribe itself
        if 'unsubscribe' in self.subscription['permissions'] and is_self_operation(self.request):
            acl.append((Allow, self.request.authenticated_userid, permissions.remove_subscription))

        return acl


class SubscriptionsTraverser(object):
    def __init__(self, parent, request):
        self.request = request
        self.db = request.registry.max_store
        self.__parent__ = parent

    def __getitem__(self, key):
        return Subscription(self, self.request, key, self.request.actor)

    @property
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.remove_subscription),
            (Allow, Owner, permissions.remove_subscription)
        ]

        return acl


def getMAXSettings(request):
    return request.registry.max_settings


def loadMAXSettings(settings):
    max_ini_settings = {key.replace('max.', 'max_'): settings[key] for key in settings.keys() if 'max' in key}
    max_ini_settings['max_message_defaults'] = {
        "source": "max",
        "domain": max_ini_settings.get('max_server_id', ''),
        "version": pkg_resources.require("max")[0].version,
    }
    return max_ini_settings


def loadCloudAPISettings(registry):
    cloudapis_settings = registry.max_store.cloudapis.find_one()
    if cloudapis_settings:
        return cloudapis_settings
    else:
        maxlogger.info("No cloudapis info found. Please run initialization database script.")  #pragma: no cover
        return DUMMY_CLOUD_API_DATA


def loadMAXSecurity(registry):
    security_settings = [a for a in registry.max_store.security.find({})]
    if security_settings:
        return security_settings[0]
    else:
        maxlogger.info("No security info found. Please run initialization database script.")  #pragma: no cover
