from pyramid.view import view_config

from max.views.api import TemplateAPI
from max.rest.utils import findKeywords


@view_config(name="maintenance", renderer='max:templates/maintenance.pt', permission='restricted')
def configView(context, request):
    page_title = "MAX Server Config"
    api = TemplateAPI(context, request, page_title)
    success = False
    message = ''
    if request.params.get('form.rebuildKeywords', None) is not None:
        db = context.db
        activities = db.activity.find({'object.content': {'$exists': True}})
        for activity in activities:

            keywords = findKeywords(activity['object']['content'])
            db.activity.update({'_id': activity['_id']}, {'$set': {'object._keywords': keywords}})
        success = True
        message = 'Keywords rebuilded!'

    return dict(api=api,
                url='%s/maintenance' % api.getAppURL(),
                success=success,
                message=message)
