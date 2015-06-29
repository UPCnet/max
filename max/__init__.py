# -*- coding: utf-8 -*-
import logging
# logger has to be instantiated BEFORE imports of resources.*
maxlogger = logging.getLogger('max')

try:
    __import__('gevent')
except ImportError:
    GEVENT_AVAILABLE = False
else:
    GEVENT_AVAILABLE = True


from max import debug
from max.request import extract_post_data
from max.request import get_database
from max.request import get_oauth_headers
from max.request import get_request_actor
from max.request import get_request_actor_username
from max.request import get_request_creator
from max.resources import Root
from max.resources import loadCloudAPISettings
from max.resources import loadMAXSecurity
from max.resources import loadMAXSettings
from max.routes import RESOURCES
from max.security.authentication import MaxAuthenticationPolicy
from max.tweens import set_signal
from maxutils import mongodb

from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.settings import asbool
from pyramid_beaker import set_cache_regions_from_settings

import os

DEFAULT_CONTEXT_PERMISSIONS = dict(
    read='restricted',
    write='restricted',
    subscribe='restricted',
    unsubscribe='restricted',
    invite='restricted',
    kick='restricted',
    delete='restricted',
    flag='restricted'
)

CONVERSATION_PARTICIPANTS_LIMIT = 20
LAST_AUTHORS_LIMIT = 8
AUTHORS_SEARCH_MAX_QUERIES_LIMIT = 6
ALLOWED_ROLES = ['Manager', 'NonVisible', 'HubManager']
DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY = True
PAGINATION_MODIFIERS = ['before', 'after', 'limit']
SORTING_MODIFIERS = ['sort', 'priority']
FILTERING_MODIFIERS = ['date_filter', 'hashtag', 'actor', 'keywords', 'tags', 'favorites', 'context_tags']
SEARCH_MODIFIERS = PAGINATION_MODIFIERS + SORTING_MODIFIERS + FILTERING_MODIFIERS
import logging

logger = logging.getLogger('exceptions')


def main(*args, **settings):
    """ This function returns a WSGI application.
    """
    # App config

    authz_policy = ACLAuthorizationPolicy()
    authn_policy = MaxAuthenticationPolicy(['widgetcli'])

    # IMPORTANT NOTE !! Order matters! Last tween added will be the first to be invoked
    settings['pyramid.tweens'] = [
        'max.tweens.excview_tween_factory',
        'max.tweens.compatibility_checker_factory',
        'max.tweens.post_tunneling_factory',
        'max.tweens.deprecation_wrapper_factory',
        'max.tweens.mongodb_probe_factory'
    ]

    debug.setup(settings)

    config = Configurator(
        settings=settings,
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
        root_factory=Root)

    config.add_request_method(get_request_actor_username, name='actor_username', reify=True)
    config.add_request_method(get_request_actor, name='actor', reify=True)
    config.add_request_method(get_request_creator, name='creator', reify=True)
    config.add_request_method(get_database, name='db', reify=True)
    config.add_request_method(extract_post_data, name='decoded_payload', reify=True)
    config.add_request_method(get_oauth_headers, name='auth_headers', reify=True)

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
        route_params = {param: value for param, value in properties.items() if param in ['traverse']}
        config.add_route(name, properties.get('route'), **route_params)

    config.scan('max', ignore=['max.tests'])
    set_signal()

    # Create exceptions log folfer if it doesnt exists
    exceptions_folder = config.registry.settings.get('exceptions_folder', '/tmp/exceptions/')
    if not os.path.exists(exceptions_folder):
        os.makedirs(exceptions_folder)

    return config.make_wsgi_app()
