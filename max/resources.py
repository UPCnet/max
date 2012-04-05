import pymongo
from pyramid.security import Everyone, Allow, Authenticated
from pyramid.settings import asbool


class Root(object):
    __parent__ = __name__ = None
    __acl__ = [
        (Allow, Everyone, 'anonymous'),
        (Allow, Authenticated, 'restricted'),
        (Allow, 'operations', 'operations'),
        (Allow, 'admin', 'admin')
        ]

    def __init__(self, request):
        self.request = request
        # MongoDB:
        registry = self.request.registry
        self.db = registry.max_store


def getMAXSettings(request):
    return request.registry.max_settings


def loadMAXSettings(settings, config):
    max_ini_settings = {key.replace('max.', 'max_'): settings[key] for key in settings.keys() if 'max' in key}
    return max_ini_settings
