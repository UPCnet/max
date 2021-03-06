# -*- coding: utf-8 -*-
from max.models import Activity
from max.rest import JSONResourceEntity

from pyramid.view import view_config


@view_config(route_name='follow', request_method='POST')
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
    newactivity = Activity.from_request(request, rest_params=rest_params)

    code = 201
    newactivity_oid = newactivity.insert()
    newactivity['_id'] = newactivity_oid

    request.actor.addFollower(newactivity['object'])

    handler = JSONResourceEntity(request, newactivity.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='follow', request_method='DELETE')
def unfollow(context, request):
    """
    """
    pass
