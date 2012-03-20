from pyramid.view import view_config

from max.models import Activity
from max.decorators import MaxRequest, MaxResponse

from max.rest.ResourceHandlers import JSONResourceEntity


@view_config(route_name='admin_user_activities', request_method='POST', permission='admin')
@MaxResponse
@MaxRequest
def addAdminUserActivity(context, request):
    """
         /admin/people/{username}/activities

         Add activity impersonated as a valid MAX user
    """
    rest_params = {'actor': request.actor,
                   'verb': 'post'}

    # Initialize a Activity object from the request
    newactivity = Activity(request, rest_params=rest_params)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newactivity.get('_id'):
        # Already Exists
        code = 200
    else:
        # New User
        code = 201
        activity_oid = newactivity.insert()
        newactivity['_id'] = activity_oid

    handler = JSONResourceEntity(newactivity.flatten(), status_code=code)
    return handler.buildResponse()
