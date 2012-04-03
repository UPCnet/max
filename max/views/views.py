from pyramid.view import view_config
from pyramid.renderers import render_to_response
from pyramid.response import Response

import requests
from urllib2 import urlparse

from max.resources import Root
from max.rest.services import WADL


@view_config(context=Root)
def rootView(context, request):

    message = 'I am a max server'
    response = Response(message)
    return response


@view_config(route_name="wadl", context=Root)
def WADLView(context, request):

    renderer = 'max:templates/wadl.pt'
    response = render_to_response(renderer,
                              dict(wadl=WADL),
                              request=request)
    response.content_type = 'application/xml'
    return response


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
