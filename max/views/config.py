from pyramid.view import view_config
from pyramid.response import Response

from max.views.api import TemplateAPI

DEFAULT_OAUTH_CHECK_ENDPOINT = 'https://oauth.upc.edu/checktoken'
DEFAULT_OAUTH_GRANT_TYPE = 'password'


@view_config(name="control_panel", renderer='max:templates/config.pt', permission='restricted')
def configView(context, request):
    page_title = "MAX Server Config"
    api = TemplateAPI(context, request, page_title)
    success = False

    config = context.db.config.find_one()
    if not config:
        config = dict(oauth_check_endpoint=DEFAULT_OAUTH_CHECK_ENDPOINT,
                      oauth_grant_type=DEFAULT_OAUTH_GRANT_TYPE)

    if request.params.get('form.submitted', None) is not None:
        config['oauth_check_endpoint'] = request.POST.get('oauth_check_endpoint')
        config['oauth_grant_type'] = request.POST.get('oauth_grant_type')

        # Save config data
        context.db.config.save(config)
        success = True

    return dict(api=api, url=request.path_url,
                oauth_check_endpoint=config.get('oauth_check_endpoint', DEFAULT_OAUTH_CHECK_ENDPOINT),
                oauth_grant_type=config.get('oauth_grant_type', DEFAULT_OAUTH_GRANT_TYPE),
                success=success
                )
