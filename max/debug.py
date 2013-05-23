from pyramid.settings import asbool


def patched_checkToken(url, username, token, scope):
    return True


def setup(config, settings):

    if asbool(settings['max.debug_api']):
        config.add_tween('max.tweens.browser_debug_factory', under='pyramid_debugtoolbar.toolbar_tween_factory')

    if asbool(settings['max.oauth_passtrough']):
        import max.oauth2
        max.oauth2.checkToken = patched_checkToken
