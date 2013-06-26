from pyramid.security import Everyone, Allow, Authenticated

from max import maxlogger


class Root(object):
    __parent__ = __name__ = None
    __acl__ = [(Allow, Everyone, 'anonymous'),
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


def loadCloudAPISettings(registry):
    cloudapis_settings = registry.max_store.cloudapis.find_one()
    if cloudapis_settings:
        return cloudapis_settings
    else:
        maxlogger.info("No cloudapis info found. Please run initialization database script.")  #pragma: no cover


def loadMAXSecurity(registry):
    security_settings = [a for a in registry.max_store.security.find({})]
    if security_settings:
        return security_settings[0]
    else:
        maxlogger.info("No security info found. Please run initialization database script.")  #pragma: no cover
