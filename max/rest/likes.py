# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented


@view_config(route_name='user_likes', request_method='GET')
def getUserLikedActivities(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='likes', request_method='GET')
def getActivityLikes(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='like', request_method='GET')
def getActivityLike(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='likes', request_method='POST')
def like(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='like', request_method='DELETE')
def unlike(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover
