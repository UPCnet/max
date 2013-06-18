# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented


@view_config(route_name='user_shares', request_method='GET')
def getUserSharedActivities(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='shares', request_method='GET')
def getActivityShares(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='share', request_method='GET')
def getActivityShare(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='shares', request_method='POST')
def share(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='share', request_method='DELETE')
def unshare(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover
