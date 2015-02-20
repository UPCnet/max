# -*- coding: utf-8 -*-
from max.decorators import MaxResponse
from max.decorators import requirePersonActor
from max.oauth2 import oauth2
from max.rest.ResourceHandlers import JSONResourceEntity

from pyramid.view import view_config

import pkg_resources
import re


@view_config(route_name='info', request_method='GET')
def getMaxPublicInfo(context, request):
    """
        /info

        Returns max server settings, only the ones allowed unauthenticad
    """
    allowed_settings = [
        'max.oauth_server',
        'max.stomp_server',
        'max.server_id'
    ]

    max_settings = request.registry.settings
    settings = {}
    for setting in allowed_settings:
        if setting in max_settings:
            settings[setting] = max_settings[setting]

    settings['version'] = pkg_resources.require("max")[0].version
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
    settings['version'] = pkg_resources.require("max")[0].version

    handler = JSONResourceEntity(settings)
    return handler.buildResponse()
