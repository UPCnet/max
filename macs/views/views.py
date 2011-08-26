from pyramid.view import view_config
from pyramid.response import Response

import pymongo

from macs.resources import Root
from macs.views.api import TemplateAPI


@view_config(context=Root, renderer='macs:templates/activityStream.pt')
def rootView(context, request):

    #page_title = "%s's Activity Stream" % username
    page_title = "Victor's Activity Stream"
    api = TemplateAPI(context, request, page_title)
    return dict(api=api)
