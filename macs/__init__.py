from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from macs.resources import Root

from macs.models import appmaker


def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    # Security
    my_session_factory = UnencryptedCookieSessionFactoryConfig('itsaseekreet')
    whoconfig_file = 'who.ini'
    identifier_id = 'auth_tkt'
    authn_policy = WhoV2AuthenticationPolicy(whoconfig_file, identifier_id)
    authz_policy = ACLAuthorizationPolicy()

    # engine = engine_from_config(settings, 'sqlalchemy.')
    # get_root = appmaker(engine)
    config = Configurator(settings=settings,
                          root_factory=Root,
                          session_factory=my_session_factory,
                          authentication_policy=authn_policy,
                          authorization_policy=authz_policy)
    config.add_static_view('static', 'macs:static')
    config.add_static_view('css', 'macs:css')
    config.add_static_view('js', 'macs:js')
    config.add_static_view('fonts', 'macs:static/fonts')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_view('macs.views.login.login', route_name='login',
                     renderer='macs:templates/login.pt')
    config.add_view('macs.views.login.logout', route_name='logout')
    config.add_view('macs.views.login.login',
                    context='pyramid.httpexceptions.HTTPForbidden',
                    renderer='macs:templates/login.pt')

    config.add_route('activity', '/activity/{id}')
    config.add_route('profiles', '/profiles/{displayName}')

    config.scan('macs')

    return config.make_wsgi_app()
