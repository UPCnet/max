from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadRequest

from pyramid.security import authenticated_userid

from max.views.api import TemplateAPI

from bson.objectid import ObjectId


#@view_config(route_name='activity', permission='restricted')
def activityView(context, request):
    activity_id = ObjectId(request.matchdict['id'])

    activity = context.db.activity.find_one(activity_id)

    return Response(str(activity))


@view_config(route_name='profiles', renderer='max:templates/profile.pt', permission='restricted')
def profilesView(context, request):

    username = request.matchdict['username']

    userprofile = context.db.users.find_one({'username': username})

    current_username = authenticated_userid(request)
    if not userprofile:
        return HTTPBadRequest('No such user')

    # Render follow button?
    if current_username == username:
        showFollowButton = False
    else:
        showFollowButton = True

    # Follow status of the current user on the viewed user profile
    current_user = context.db.users.find_one({'username': current_username}, {'following': 1})

    isFollowing = False
    for following in current_user['following']['items']:
        if following['username'] == userprofile['username']:
            isFollowing = True
            break

    followinfo = {'showFollowButton': showFollowButton, 'isFollowing': isFollowing}

    # import ipdb;ipdb.set_trace()

    page_title = "%s's User Profile" % userprofile
    api = TemplateAPI(context, request, page_title)
    return dict(api=api, userprofile=userprofile, followinfo=followinfo)
