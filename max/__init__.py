# -*- coding: utf-8 -*-
import logging
# logger has to be instantiated BEFORE the import of the following resources import
maxlogger = logging.getLogger('max')

try:
    __import__('gevent')
except ImportError:
    GEVENT_AVAILABLE = False
else:
    GEVENT_AVAILABLE = True

from max import patches
from max.resources import Root
from max.resources import loadCloudAPISettings
from max.resources import loadMAXSecurity
from max.resources import loadMAXSettings
from max.rest.resources import RESOURCES

from pyramid.config import Configurator
from pyramid.settings import asbool
from pyramid_beaker import set_cache_regions_from_settings

from max import debug
from max.predicates import RestrictedPredicate
from max.decorators import set_signal

from maxutils import mongodb

DEFAULT_CONTEXT_PERMISSIONS = dict(read='restricted', write='restricted', subscribe='restricted', invite='restricted', delete='restricted', flag='restricted')
CONVERSATION_PARTICIPANTS_LIMIT = 20
LAST_AUTHORS_LIMIT = 8
AUTHORS_SEARCH_MAX_QUERIES_LIMIT = 6
ALLOWED_ROLES = ['Manager', 'NonVisible', 'HubManager']
DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY = True


def main(*args, **settings):
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

    # Mongodb connection initialization
    cluster_enabled = asbool(settings.get('mongodb.cluster', False))
    auth_enabled = asbool(settings.get('mongodb.auth', False))
    mongodb_uri = settings.get('mongodb.hosts') if cluster_enabled else settings['mongodb.url']

    conn = mongodb.get_connection(
        mongodb_uri,
        use_greenlets=GEVENT_AVAILABLE,
        cluster=settings.get('mongodb.replica_set', None))
    db = mongodb.get_database(
        conn,
        settings['mongodb.db_name'],
        username=settings.get('mongodb.username', None) if auth_enabled else None,
        password=settings.get('mongodb.password', None) if auth_enabled else None,
        authdb=settings.get('mongodb.authdb', None) if auth_enabled else None)

    config.registry.max_store = db

    # Set MAX settings
    config.registry.max_settings = loadMAXSettings(settings)

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
    set_signal()
    return config.make_wsgi_app()
