# -*- coding: utf-8 -*-
import logging
import pymongo

from pyramid.config import Configurator

# logger has to be BEFORE the import of the following resources import
maxlogger = logging.getLogger('max')

from max.resources import Root, loadMAXSettings, loadMAXSecurity
from max.rest.resources import RESOURCES

DEFAULT_CONTEXT_PERMISSIONS = dict(read='public', write='public', join='public', invite='public')


def main(global_config, **settings):
    """ This function returns a WSGI application.
    """

    # App config
    config = Configurator(settings=settings,
                          root_factory=Root)

    config.add_route('wadl', '/WADL')

    # Store in registry
    db_uri = settings['mongodb.url']
    conn = pymongo.Connection(db_uri)
    db = conn[settings['mongodb.db_name']]
    config.registry.max_store = db

    # Set MAX settings
    config.registry.max_settings = loadMAXSettings(settings, config)

    # Set security
    config.registry.max_security = loadMAXSecurity(config.registry)

    # REST Resources
    # Configure routes based on resources defined in RESOURCES
    for name, properties in RESOURCES.items():
        config.add_route(name, properties.get('route'))

    config.scan('max', ignore='max.tests')

    return config.make_wsgi_app()
