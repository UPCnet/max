from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest

from pyramid.security import authenticated_userid

from macs.resources import Root
from macs.views.api import TemplateAPI, activityAPI

from bson.objectid import ObjectId


@view_config(route_name='activity', permission='restricted')
def activityView(context, request):
    activity_id = ObjectId(request.matchdict['id'])

    activity = context.db.activity.find_one(activity_id)

    username = authenticated_userid(request)
    page_title = "%s's Activity Stream" % username
    # page_title = "Victor's Activity Stream"
    api = TemplateAPI(context, request, page_title)
    aapi = activityAPI(context, request)
    # return dict(api=api, aapi=aapi)
    return Response(str(activity))


@view_config(route_name='profiles', renderer='macs:templates/profile.pt', permission='restricted')
def profilesView(context, request):

    displayName = request.matchdict['displayName']

    user = context.db.users.find_one({'displayName': displayName})

    if not user:
        return HTTPBadRequest('No such user')

    username = authenticated_userid(request)
    page_title = "%s's Activity Stream" % username
    # page_title = "Victor's Activity Stream"
    api = TemplateAPI(context, request, page_title)
    aapi = activityAPI(context, request)
    return dict(api=api, aapi=aapi, user=user)
