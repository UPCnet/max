from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest

from pyramid.security import authenticated_userid

from max.views.api import TemplateAPI, activityAPI

from bson.objectid import ObjectId


#@view_config(route_name='activity', permission='restricted')
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


@view_config(route_name='profiles', renderer='max:templates/profile.pt', permission='restricted')
def profilesView(context, request):

    displayName = request.matchdict['displayName']

    userprofile = context.db.users.find_one({'displayName': displayName})

    current_username = authenticated_userid(request)
    if not userprofile:
        return HTTPBadRequest('No such user')

    # Render follow button?
    if current_username == displayName:
        showFollowButton = False
    else:
        showFollowButton = True

    # Follow status of the current user on the viewed user profile
    current_user = context.db.users.find_one({'displayName': current_username}, {'following': 1})

    isFollowing = False
    for following in current_user['following']['items']:
        if following['displayName'] == userprofile['displayName']:
            isFollowing = True
            break

    followinfo = {'showFollowButton': showFollowButton, 'isFollowing': isFollowing}

    # import ipdb;ipdb.set_trace()

    page_title = "%s's User Profile" % userprofile
    api = TemplateAPI(context, request, page_title)
    aapi = activityAPI(context, request)
    return dict(api=api, aapi=aapi, userprofile=userprofile, followinfo=followinfo)
