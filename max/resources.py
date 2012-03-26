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
    db = config.registry.max_store
    max_ini_settings = {key.replace('max.', 'max_'): settings[key] for key in settings.keys() if 'max' in key}
    if asbool(max_ini_settings.get('max_enforce_settings')) == True:
        # Enforce ini settings
        return max_ini_settings
    else:
        # Try to find config in store
        config_doc = db.config.find_one()
        if not config_doc:
            # No settings in store, return the ini settings
            return max_ini_settings
        else:
            max_db_settings = {key: config_doc[key] for key in config_doc.keys() if 'max' in key}
            return max_db_settings
