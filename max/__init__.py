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
from max.decorators import set_signal
from max.predicates import RequiredActorPredicate
from max.predicates import RestrictedPredicate
from max.resources import loadCloudAPISettings
from max.resources import loadMAXSecurity
from max.resources import loadMAXSettings
from max.resources import Root
from max.rest.resources import RESOURCES
from max.security.authentication import MaxAuthenticationPolicy
from maxutils import mongodb
from max.request import get_request_creator
from max.request import get_request_actor_username
from max.request import get_request_actor
from max.request import get_authenticated_user_roles
from max.request import get_database
from max.request import extract_post_data, get_oauth_headers
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.settings import asbool
from pyramid_beaker import set_cache_regions_from_settings


DEFAULT_CONTEXT_PERMISSIONS = dict(
    read='restricted',
    write='restricted',
    subscribe='restricted',
    invite='restricted',
    delete='restricted',
    flag='restricted')
CONVERSATION_PARTICIPANTS_LIMIT = 20
LAST_AUTHORS_LIMIT = 8
AUTHORS_SEARCH_MAX_QUERIES_LIMIT = 6
ALLOWED_ROLES = ['Manager', 'NonVisible', 'HubManager']
DEFAULT_CONTEXT_PERMISSIONS_PERMANENCY = True


def main(*args, **settings):
    """ This function returns a WSGI application.
    """
    # App config

    authz_policy = ACLAuthorizationPolicy()
    authn_policy = MaxAuthenticationPolicy(['widgetcli'])

    config = Configurator(
        settings=settings,
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
        root_factory=Root)

    # IMPORTANT NOTE !! Order matters! Last tween added will be the first to be invoked
    config.add_tween('pyramid.tweens.excview_tween_factory')
    config.add_tween('max.tweens.deprecation_wrapper_factory')
    config.add_tween('max.tweens.post_tunneling_factory')
    config.add_tween('max.tweens.compatibility_checker_factory')

    config.add_request_method(get_request_actor_username, name='actor_username', reify=True)
    config.add_request_method(get_request_actor, name='actor', reify=True)
    config.add_request_method(get_request_creator, name='creator', reify=True)
    config.add_request_method(get_authenticated_user_roles, name='roles', reify=True)
    config.add_request_method(get_database, name='db', reify=True)
    config.add_request_method(extract_post_data, name='decoded_payload', reify=True)
    config.add_request_method(get_oauth_headers, name='auth_headers', reify=True)

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
        route_params = {param: value for param, value in properties.items() if param in ['traverse']}
        config.add_route(name, properties.get('route'), **route_params)

    config.scan('max', ignore=['max.tests', 'max.scripts'])

    config.add_view_predicate('restricted', RestrictedPredicate)
    config.add_view_predicate('requires_actor', RequiredActorPredicate)
    set_signal()
    return config.make_wsgi_app()
