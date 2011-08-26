import pymongo


class Root(object):
    __parent__ = __name__ = None

    def __init__(self, request):
        self.request = request
        # MongoDB:
        settings = self.request.registry.settings
        db_uri = settings['mongodb.url']
        conn = pymongo.Connection(db_uri)
        self.db = conn[settings['mongodb.db_name']]
