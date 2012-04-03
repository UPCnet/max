from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent

from max.models import Activity
from max.decorators import MaxRequest, MaxResponse
from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceEntity
from max.rest.ResourceHandlers import JSONResourceRoot
from max.exceptions import ObjectNotFound


@view_config(route_name='admin_user_activities', request_method='POST', permission='admin')
#@MaxResponse
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


@view_config(route_name='admin_users', request_method='GET', permission='operations')
@MaxResponse
@MaxRequest
def getUsers(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    users = mmdb.users.dump(flatten=1)
    handler = JSONResourceRoot(users)
    return handler.buildResponse()


@view_config(route_name='admin_activities', request_method='GET', permission='operations')
@MaxResponse
@MaxRequest
def getActivities(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    activities = mmdb.activity.dump(flatten=1)
    handler = JSONResourceRoot(activities)
    return handler.buildResponse()


@view_config(route_name='admin_contexts', request_method='GET', permission='operations')
@MaxResponse
@MaxRequest
def getContexts(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    contexts = mmdb.contexts.dump(flatten=1)
    handler = JSONResourceRoot(contexts)
    return handler.buildResponse()


@view_config(route_name='admin_user', request_method='DELETE', permission='operations')
@MaxResponse
@MaxRequest
def deleteUser(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    userid = request.matchdict.get('id', None)
    try:
        found_user = mmdb.users[userid]
    except:
        raise ObjectNotFound, "There's no user with id: %s" % userid

    found_user.delete()
    return HTTPNoContent()


@view_config(route_name='admin_activity', request_method='DELETE', permission='operations')
@MaxResponse
@MaxRequest
def deleteActivity(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    activityid = request.matchdict.get('id', None)
    try:
        found_activity = mmdb.activity[activityid]
    except:
        raise ObjectNotFound, "There's no activity with id: %s" % activityid

    found_activity.delete()
    return HTTPNoContent()


@view_config(route_name='admin_context', request_method='DELETE', permission='operations')
@MaxResponse
@MaxRequest
def deleteContext(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    contextid = request.matchdict.get('id', None)
    try:
        found_context = mmdb.contexts[contextid]
    except:
        raise ObjectNotFound, "There's no context with id: %s" % contextid

    found_context.delete()

    # XXX in admin too ?
    #found_context[0].removeUserSubscriptions()
    return HTTPNoContent()
