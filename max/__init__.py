# -*- coding: utf-8 -*-
import logging
import pymongo
from max import patches
from pyramid.config import Configurator

# logger has to be instantiated BEFORE the import of the following resources import
maxlogger = logging.getLogger('max')

from max.resources import Root
from max.resources import loadMAXSettings
from max.resources import loadMAXSecurity
from max.resources import loadCloudAPISettings
from max.rest.resources import RESOURCES

from pyramid_beaker import set_cache_regions_from_settings
from pyramid.settings import asbool
from max import debug
from predicates import RestrictedPredicate

DEFAULT_CONTEXT_PERMISSIONS = dict(read='public', write='public', subscribe='public', invite='public', delete='restricted')
CONVERSATION_PARTICIPANTS_LIMIT = 20
LAST_AUTHORS_LIMIT = 8
AUTHORS_SEARCH_MAX_QUERIES_LIMIT = 6
ALLOWED_ROLES = ['Manager', 'NonVisible']


def main(global_config, **settings):
    """ This function returns a WSGI application.
    """

    # App config
    config = Configurator(settings=settings,
                          root_factory=Root)

    # IMPORTANT NOTE !! Order matters! Last tween added will be the first to be invoked
    config.add_tween('max.tweens.post_tunneling_factory')
    config.add_tween('max.tweens.compatibility_checker_factory')

    debug.setup(config, settings)

    config.add_route('wadl', '/WADL')

    # Store in registry
    if not asbool(settings.get('mongodb.cluster', False)):
        db_uri = settings['mongodb.url']
        conn = pymongo.MongoClient(db_uri)
    else:
        hosts = settings.get('mongodb.hosts', '')
        replica_set = settings.get('mongodb.replica_set', '')
        conn = pymongo.MongoReplicaSetClient(hosts, replicaSet=replica_set, use_greenlets=True)

    db = conn[settings['mongodb.db_name']]
    config.registry.max_store = db

    # Set MAX settings
    config.registry.max_settings = loadMAXSettings(settings, config)

    # Set Twitter settings
    config.registry.cloudapis_settings = loadCloudAPISettings(config.registry)

    # Set security
    config.registry.max_security = loadMAXSecurity(config.registry)

    # Load cache settings
    set_cache_regions_from_settings(settings)

    # REST Resources
    # Configure routes based on resources defined in RESOURCES
    for name, properties in RESOURCES.items():
        config.add_route(name, properties.get('route'))

    config.scan('max', ignore=['max.tests', 'max.scripts'])

    config.add_view_predicate('restricted', RestrictedPredicate)

    return config.make_wsgi_app()
