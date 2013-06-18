# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented

from max.decorators import MaxResponse, requirePersonActor
from max.models import Activity
from max.oauth2 import oauth2
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
@oauth2(['widgetcli'])
@requirePersonActor
def follow(context, request):
    """
        /people/{username}/follows/{followedUsername}'
    """
    #XXX TODO ara nomes es tracta un sol follow
    # s'ha de iterar si es vol que el comentari sigui de N follows
    rest_params = {
        'actor': request.actor,
        'verb': 'follow',
        'object': {
            'username': request.matchdict['followedUsername'],
            'objectType': 'person'
        }
    }

    # Initialize a Activity object from the request
    newactivity = Activity()
    newactivity.fromRequest(request, rest_params=rest_params)

    code = 201
    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    request.actor.addFollower(newactivity['object'])

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='follow', request_method='DELETE')
def unfollow(context, request):
    """
    """
    return HTTPNotImplemented()  # pragma: no cover
