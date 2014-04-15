# -*- coding: utf-8 -*-
from pyramid.view import view_config
from max.oauth2 import oauth2
from max.decorators import MaxResponse, requirePersonActor
from max.rest.ResourceHandlers import JSONResourceEntity

from max.resources import getMAXSettings
import re


@view_config(route_name='info', request_method='GET')
def getMaxPublicInfo(context, request):
    """
        /info

        Returns max server settings, only the ones allowed unauthenticad
    """
    allowed_settings = [
        'max.oauth_server'
    ]

    max_settings = request.registry.settings
    settings = {}
    for setting in allowed_settings:
        settings[setting] = max_settings[setting]

    handler = JSONResourceEntity(settings)
    return handler.buildResponse()


@view_config(route_name='info_settings', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getMaxSettings(context, request):
    """
        /info/settings

        Returns all max server settings
    """
    max_settings = request.registry.settings
    settings = {key: value for key, value in max_settings.items() if re.match('^(max|mongodb|cache|oauth)', key)}
    handler = JSONResourceEntity(settings)
    return handler.buildResponse()
