import pymongo
from pyramid.security import Everyone, Allow, Authenticated


class Root(object):
    __parent__ = __name__ = None
    __acl__ = [
        (Allow, Everyone, 'anonymous'),
        (Allow, Authenticated, 'restricted'),
        (Allow, 'operations', 'manage')
        ]

    def __init__(self, request):
        self.request = request
        # MongoDB:
        settings = self.request.registry.settings
        self.db = settings.max_store


def getMAXSettings(context):
    config = context.db.config.find_one()
    return config


def setMAXSettings(config):
    import ipdb; ipdb.set_trace( )
    db = config.registry.max_store
    config_doc = db.config.find_one()
    if not config_doc:
        config_doc = {}
        config_doc['oauth_checkpoint'] = config.registry.settings.get('max.oauth_check_endpoint')
        db.config.save(config_doc)
    else:
        config.registry.settings['max.oauth_check_endpoint'] = config_doc.get('max.oauth_check_endpoint')
