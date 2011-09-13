from pyramid.view import view_config
from pyramid.response import Response

from pyramid.security import authenticated_userid

import pymongo

from macs.resources import Root
from macs.views.api import TemplateAPI, activityAPI


@view_config(context=Root, renderer='macs:templates/activityStream.pt', permission='restricted')
def rootView(context, request):

    username = authenticated_userid(request)
    page_title = "%s's Activity Stream" % username
    api = TemplateAPI(context, request, page_title)
    aapi = activityAPI(context, request)
    return dict(api=api, aapi=aapi)


@view_config(name='js_variables.js', context=Root, renderer='macs:templates/js_variables.js.pt', permission='restricted')
def js_variables(context, request):

    username = authenticated_userid(request)
    userid = context.db.users.find_one({'displayName': username}, {'_id': 1})

    variables = {'username': username,
                 'userid': str(userid['_id']),
    }
    return dict(variables=variables)
