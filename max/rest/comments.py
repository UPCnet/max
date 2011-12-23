# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError, HTTPNotImplemented

from max.exceptions import MissingField
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
from max.decorators import MaxRequest, MaxResponse
from max.models import Activity

from pymongo.objectid import ObjectId


@view_config(route_name='user_comments', request_method='GET')
@MaxResponse
@MaxRequest
def getUserComments(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='comments', request_method='GET')
@MaxResponse
@MaxRequest
def getActivityComments(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='comments', request_method='POST')
@MaxResponse
@MaxRequest
def addActivityComment(context, request):
    """
    POST /activities/{activity}/comments
    """
    #XXX TODO ara només es tracta la primera activitat,
    # s'ha de iterar si es vol que el comentari sigui de N activitats
    activityid = request.matchdict['activity']

    mmdb = MADMaxDB(context.db)
    refering_activity = mmdb.activity[activityid]

    # Prepare rest parameters to be merged with post data
    rest_params = {'object': {'inReplyTo': [{'_id':ObjectId(activityid)}]}}

    # Initialize a Activity object from the request
    newactivity = Activity(request, rest_params=rest_params)

    code = 201
    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    comment = dict(newactivity.object)
    comment['author'] = {'displayName': newactivity.actor['displayName']}
    comment['id'] = newactivity._id
    del comment['inReplyTo']

    refering_activity.addComment(comment)

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='comment', request_method='GET')
def getActivityComment(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='comments', request_method='PUT')
def modifyActivityComments(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='comments', request_method='DELETE')
def deleteActivityComments(context, request):
    """
    """
    return HTTPNotImplemented()
