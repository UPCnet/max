from pyramid.config import Configurator

from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from max.resources import Root, loadMAXSettings
from max.rest.resources import RESOURCES

import pymongo

DEFAULT_CONTEXT_PERMISSIONS = dict(read='public', write='public', join='public', invite='public')


def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    # Security
    my_session_factory = UnencryptedCookieSessionFactoryConfig('itsaseekreet')
    whoconfig_file = settings['whoconfig_file']
    identifier_id = 'auth_tkt'
    authn_policy = WhoV2AuthenticationPolicy(whoconfig_file, identifier_id)
    authz_policy = ACLAuthorizationPolicy()

    # App config
    config = Configurator(settings=settings,
                          root_factory=Root,
                          session_factory=my_session_factory,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy)
    config.add_static_view('static', 'max:static')
    config.add_static_view('css', 'max:css')
    config.add_static_view('less', 'max:less')
    config.add_static_view('js', 'max:js')
    config.add_static_view('fonts', 'max:static/fonts')
    config.add_static_view('maxui', 'max:maxui')

    config.add_route('profiles', '/profiles/{username}')
    config.add_route('wadl', '/WADL')

    # Store in registry
    db_uri = settings['mongodb.url']
    conn = pymongo.Connection(db_uri)
    db = conn[settings['mongodb.db_name']]
    config.registry.max_store = db

    # Set MAX settings
    config.registry.max_settings = loadMAXSettings(settings, config)

    # REST Resources
    # Configure routes based on resources defined in RESOURCES
    for name, properties in RESOURCES.items():
        config.add_route(name, properties.get('route'))

    config.scan('max', ignore='max.tests')

    return config.make_wsgi_app()
