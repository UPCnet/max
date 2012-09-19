# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.response import Response

from pyramid.httpexceptions import HTTPBadRequest, HTTPOk, HTTPNotImplemented

import json
from bson import json_util
from bson.objectid import ObjectId

from max.resources import Root
from max.rest.utils import checkIsValidActivity, checkDataShare, checkIsValidUser, checkRequestConsistency, extractPostData

import time
from rfc3339 import rfc3339
from copy import deepcopy


@view_config(route_name='user_likes', request_method='GET')
def getUserLikedActivities(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='likes', request_method='GET')
def getActivityLikes(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='like', request_method='GET')
def getActivityLike(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='likes', request_method='POST')
def like(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='like', request_method='DELETE')
def unlike(context, request):
    """
    """
    return HTTPNotImplemented()
