# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.response import Response

from max.resources import Root


@view_config(context=Root)
def rootView(context, request):

    message = 'I am a max server'
    response = Response(message)
    return response
