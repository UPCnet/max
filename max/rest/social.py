# -*- coding: utf-8 -*-
from max.MADMax import MADMaxDB
from max.exceptions import Forbidden
from max.exceptions import ObjectNotFound
from max.exceptions import Unauthorized
from max.rest.ResourceHandlers import JSONResourceEntity


from pyramid.httpexceptions import HTTPNoContent
from max.rest import endpoint
from max.security.permissions import flag_activity, unflag_activity


@endpoint(route_name='flag', request_method='POST', requires_actor=True, permission=flag_activity)
def flagActivity(context, request):
    """
         Sets the flagged mark on an activity
    """
    mmdb = MADMaxDB(request.db)
    activityid = request.matchdict.get('activity', None)
    try:
        found_activity = mmdb.activity[activityid]
    except:
        raise ObjectNotFound("There's no activity with id: %s" % activityid)

    status_code = 200
    # Check if the activity is flaggable by the actor
    if found_activity.get('contexts', []):
        ctxt = found_activity.contexts[0]
        subscription = request.actor.getSubscription(ctxt)
        if 'flag' not in subscription['permissions']:
            raise Unauthorized("You are not allowed to flag this activity.")

        # Flag only if not already flagged
        if found_activity.get('flagged', None) is None:
            found_activity.flag()
            found_activity.save()
            status_code = 201

    else:
        raise Forbidden("Only context activities can be flagged.")

    handler = JSONResourceEntity(found_activity.flatten(), status_code=status_code)
    return handler.buildResponse()


@endpoint(route_name='flag', request_method='DELETE', requires_actor=True, permission=unflag_activity)
def unflagActivity(context, request):
    """
         Unsets the flagged mark on an activity
    """
    mmdb = MADMaxDB(request.db)
    activityid = request.matchdict.get('activity', None)
    try:
        found_activity = mmdb.activity[activityid]
    except:
        raise ObjectNotFound("There's no activity with id: %s" % activityid)

    # Check if the activity is flaggable by the actor
    if found_activity.get('contexts', []):
        ctxt = found_activity.contexts[0]
        subscription = request.actor.getSubscription(ctxt)
        if 'flag' not in subscription['permissions']:
            raise Unauthorized("You are not allowed to unflag this activity.")
    else:
        raise Forbidden("Only context activities can be unflagged.")

    found_activity.unflag()
    found_activity.save()

    return HTTPNoContent()
