# -*- coding: utf-8 -*-
from max import maxlogger
from max.MADMax import MADMaxCollection
from pyramid.security import Allow, Authenticated


from max.security import Manager
from max.security.permissions import add_context, list_contexts, delete_context, modify_context, view_context, view_stats, list_public_contexts, view_context_activity
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
            (Allow, Manager, view_stats),
            (Allow, Manager, 'Add people')
        ]

        # Grant the permission associated with the view to the authenticated user
        # ONLY when we're making a HEAD request. This way we can keep view permissions sane
        # Related to GET methods, while allowing HEAD counterpart available to the
        # requesting user
        if self.request.method == 'HEAD':
            frame = get_pyramid_authorization_frame()
            if frame:
                required_view_permission = frame.f_locals['permission']
                acl.append((Allow, Authenticated, required_view_permission))

        return acl

    def __init__(self, request):
        self.request = request
        # MongoDB:
        registry = self.request.registry
        self.db = registry.max_store
        self['contexts'] = ContextTraverser(self, request)


class ContextTraverser(object):
    def __init__(self, parent, request):
        self.request = request
        self.__parent__ = parent
        self.db = self.request.registry.max_store.contexts
        self.contexts = MADMaxCollection(self.db, query_key='hash')

    @property
    def __acl__(self):
        acl = []
        acl.extend([
            (Allow, Manager, add_context),
            (Allow, Manager, list_contexts),
            (Allow, Authenticated, list_public_contexts),
            (Allow, Manager, modify_context),
            (Allow, Manager, delete_context),
            (Allow, Manager, view_context),
            (Allow, Manager, view_context_activity)
        ])
        return acl

    def __getitem__(self, key):
        try:
            context = self.contexts[key]
            context.__parent__ = self
            return context
        except:
            raise KeyError(key)


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
