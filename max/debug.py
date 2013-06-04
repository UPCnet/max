from pyramid.settings import asbool


def patched_checkToken(url, username, token, scope, False):
    return True


def setup(config, settings):
    if asbool(settings['max.debug_api']):
        sort_order = dict(under='pyramid_debugtoolbar.toolbar_tween_factory')

        # Don't apply tween order when running from tests
        if asbool(settings.get('testing', False)):  # pragma: no cover
            sort_order = {}
        config.add_tween('max.tweens.browser_debug_factory', **sort_order)

    if asbool(settings['max.oauth_passtrough']):
        import max.oauth2
        max.oauth2.checkToken = patched_checkToken
