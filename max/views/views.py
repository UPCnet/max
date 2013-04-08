# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.renderers import render_to_response
from pyramid.response import Response

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
