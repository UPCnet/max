# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPInternalServerError, HTTPNotImplemented

from max.exceptions import MissingField
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity

from max.models import Activity

from pymongo.objectid import ObjectId


@view_config(route_name='user_comments', request_method='GET')
def getUserComments(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='comments', request_method='GET')
def getActivityComments(context, request):
    """
    """
    return HTTPNotImplemented()


@view_config(route_name='comments', request_method='POST')
def addActivityComment(context, request):
    """
    POST /activities/{activity}/comments
    """

    #XXX TODO ara només es tracta la primera activitat,
    # s'ha de iterar si es vol que el comentari sigui de N activitats
    activityid = request.matchdict['activity']

    try:
        mmdb = MADMaxDB(context.db)
        refering_activity = mmdb.activity[activityid]
    except TypeError:
        # La activitat indicada no existeix
        return HTTPBadRequest()

    # Prepare rest parameters to be merged with post data
    rest_params = {'object': {'inReplyTo': [{'_id':ObjectId(activityid)}]}}

    # Try to initialize a Activity object from the request
    # And catch the possible exceptions
    try:
        newactivity = Activity(request, rest_params=rest_params)
    except MissingField:
        return HTTPBadRequest()
    except ValueError:
        return HTTPBadRequest()
    except:
        return HTTPInternalServerError()

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
