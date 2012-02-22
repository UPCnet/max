from pyramid.view import view_config
from pyramid.renderers import render_to_response
from pyramid.security import authenticated_userid

from max.resources import Root
from max.views.api import TemplateAPI
from max.rest.services import WADL


@view_config(context=Root, renderer='max:templates/activityStream.pt', permission='restricted')
def rootView(context, request):

    username = authenticated_userid(request)
    page_title = "%s's Activity Stream" % username
    api = TemplateAPI(context, request, page_title)
    return dict(api=api)


@view_config(route_name="wadl", context=Root)
def WADLView(context, request):

    renderer = 'max:templates/wadl.pt'
    response = render_to_response(renderer,
                              dict(wadl=WADL),
                              request=request)
    response.content_type = 'application/xml'
    return response


@view_config(name='js_variables.js', context=Root, renderer='max:templates/js_variables.js.pt', permission='restricted')
def js_variables(context, request):

    username = authenticated_userid(request)
    userid = context.db.users.find_one({'username': username}, {'_id': 1})

    variables = {'username': username,
                 'userid': str(userid['_id']),
    }
    return dict(variables=variables)
