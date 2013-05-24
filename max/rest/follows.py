# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented
from max.decorators import MaxResponse

from max.models import Activity

from max.rest.ResourceHandlers import JSONResourceEntity


@view_config(route_name='follows', request_method='GET')
def getFollowedUsers(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='follow', request_method='GET')
def getFollowedUser(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover


@view_config(route_name='follow', request_method='POST')
@MaxResponse
def follow(context, request):
    """
        /people/{username}/follows/{followedDN}'
    """
    #XXX TODO ara nomes es tracta un sol follow
    # s'ha de iterar si es vol que el comentari sigui de N follows
    actor = request.actor
    rest_params = {'actor': request.actor}

    # Initialize a Activity object from the request
    newactivity = Activity(request, rest_params=rest_params)

    code = 201
    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    actor.addFollower(newactivity['object'])

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='follow', request_method='DELETE')
def unfollow(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover
