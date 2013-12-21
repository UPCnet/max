# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented
from max.decorators import MaxResponse, requirePersonActor
from max.oauth2 import oauth2


@view_config(route_name='user_likes', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getUserLikedActivities(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='likes', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getActivityLikes(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='like', request_method='GET')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def getActivityLike(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='likes', request_method='POST')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def like(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='like', request_method='DELETE')
@MaxResponse
@oauth2(['widgetcli'])
@requirePersonActor
def unlike(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover
