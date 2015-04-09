from pyramid.settings import asbool


def patched_check_token(*args, **kwargs):
    return True


def setup(settings):
    if asbool(settings['max.debug_api']):

        if asbool(settings.get('testing', False)):  # pragma: no cover
            settings['pyramid.tweens'].insert(0, 'max.tweens.browser_debug_factory')
        else:  # pragma: no cover
            settings['pyramid.tweens'].append('max.tweens.browser_debug_factory')

    if asbool(settings['max.oauth_passtrough']):
        import max.security.authentication
        max.security.authentication.check_token = patched_check_token
