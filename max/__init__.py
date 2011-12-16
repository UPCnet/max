from pyramid.config import Configurator
# from sqlalchemy import engine_from_config

from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid_who.whov2 import WhoV2AuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from max.resources import Root

# from max.models import appmaker


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
    config.add_static_view('static', 'max:static')
    config.add_static_view('css', 'max:css')
    config.add_static_view('js', 'max:js')
    config.add_static_view('fonts', 'max:static/fonts')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_view('max.views.login.login', route_name='login',
                     renderer='max:templates/login.pt')
    config.add_view('max.views.login.logout', route_name='logout')
    config.add_view('max.views.login.login',
                    context='pyramid.httpexceptions.HTTPForbidden',
                    renderer='max:templates/login.pt')

    config.add_route('profiles', '/profiles/{displayName}')

    # REST Resources

    config.add_route('users', '/users')
    config.add_route('user', '/users/{user_displayName}')

    config.add_route('activities', '/users/{user_displayName}/activities')
    config.add_route('activity', '/users/{user_displayName}/activities/{activity_oid}')

    config.add_route('timeline', '/users/{user_displayName}/timeline')
    

    config.scan('max')


    return config.make_wsgi_app()
