# -*- coding: utf-8 -*-
from max.resources import Root

from pyramid.response import Response
from pyramid.view import view_config


@view_config(context=Root)
def rootView(context, request):

    message = 'I am a max server'
    response = Response(message)
    return response
