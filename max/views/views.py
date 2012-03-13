from pyramid.view import view_config
from pyramid.renderers import render_to_response
from pyramid.security import authenticated_userid
from pyramid.response import Response
from pyramid.view import forbidden_view_config
from pyramid.httpexceptions import HTTPFound

import requests
from urllib2 import urlparse

from max.resources import Root
from max.views.api import TemplateAPI
from max.rest.services import WADL
from max.rest.resources import RESOURCES
from max.exceptions import JSONHTTPUnauthorized


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


@view_config(name='variables.js', context=Root, renderer='max:templates/js_variables.js.pt', permission='restricted')
def js_variables(context, request):

    username = authenticated_userid(request)
    config = context.db.config.find_one()

    variables = {'username': username,
                'token': request.session.get('oauth_token'),
                'server': config.get('max_max_server'),
                'grant': config.get('oauth_grant_type'),

    }
    return dict(variables=variables)


@view_config(name='makeRequest', context=Root)
def makeRequest(context, request):
    method = request.params.get('httpMethod')
    url = request.params.get('url')
    headers_qs = request.params.get('headers', '')
    headers = dict(urlparse.parse_qsl(headers_qs))
    data = request.params.get('postData')

    requester = getattr(requests, method.lower())
    resp = requester(url, headers=headers, data=data)

    response = Response(resp.text)
    response.status_int = resp.status_code
    response.headers.update(resp.headers)
    print 'finished'
    return response


@forbidden_view_config()
def forbidden(request):
    """
        Catch unauthorized requests and answer with an JSON error if is a REST service,
        and redirect to login form otherwise.
    """

    if getattr(request.matched_route, 'name', None) in RESOURCES:
        return JSONHTTPUnauthorized(error=dict(error='RestrictedService', error_description="You don't have permission to access this service"))
    else:
        return HTTPFound(location='%s/login?' % request.application_url)
