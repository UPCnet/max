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
    whoconfig_file = settings['whoconfig_file']
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
    config.add_static_view('less', 'max:less')
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

    config.add_route('profiles', '/profiles/{username}')
    config.add_route('wadl', '/WADL')

    # REST Resources

    config.add_route('users', '/people')
    config.add_route('user', '/people/{username}')
    config.add_route('avatar', '/people/{username}/avatar')

    config.add_route('user_activities', '/people/{username}/activities')
    config.add_route('timeline', '/people/{username}/timeline')
    config.add_route('user_comments', '/people/{username}/comments')
    config.add_route('user_shares', '/people/{username}/shares')
    config.add_route('user_likes', '/people/{username}/likes')
    config.add_route('follows', '/people/{username}/follows')
    config.add_route('follow', '/people/{username}/follows/{followedDN}')
    config.add_route('subscriptions', '/people/{username}/subscriptions')
    config.add_route('subscription', '/people/{username}/subscriptions/{subscrId}}')

    config.add_route('activities', '/activities')
    config.add_route('activity', '/activities/{activity}')
    config.add_route('comments', '/activities/{activity}/comments')
    config.add_route('comment', '/activities/{activity}/comments/{commentId}')
    config.add_route('likes', '/activities/{activity}/likes')
    config.add_route('like', '/activities/{activity}/likes/{likeId}')
    config.add_route('shares', '/activities/{activity}/shares')
    config.add_route('share', '/activities/{activity}/shares/{shareId}')

    config.scan('max')

    return config.make_wsgi_app()
