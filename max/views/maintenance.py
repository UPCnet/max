from pyramid.view import view_config

from max.views.api import TemplateAPI
from max.rest.utils import findKeywords


@view_config(name="maintenance", renderer='max:templates/maintenance.pt', permission='restricted')
def configView(context, request):
    page_title = "MAX Server Config"
    api = TemplateAPI(context, request, page_title)
    success = False
    message = ''
    if request.params.get('form.resetKeywords', None) is not None:
        db = context.db
        activities = db.activity.find({'object.content': {'$exists': True}})
        for activity in activities:

            keywords = findKeywords(activity['object']['content'])
            db.activity.update({'_id': activity['_id']}, {'$set': {'object._keywords': keywords}})
        success = True
        message = 'Keywords rebuilded!'

    if request.params.get('form.resetPermissions', None) is not None:
        db = context.db
        contexts = {context['url']: context for context in db.contexts.find()}
        users = db.users.find()
        for user in users:
            subscriptions = user.get('subscribedTo', {})
            items = subscriptions.get('items', [])
            if items:
                for item in items:
                    curl = item.get('url')
                    permissions = ['read']
                    context = contexts.get(curl)
                    if context:
                        if context['permissions']['write'] == 'subscribed':
                            permissions.append('write')
                        item['permissions'] = permissions
                        for field in ['displayName']:
                            if context.get(field, None):
                                item[field] = context[field]
                db.users.update({'_id': user['_id']}, {'$set': {'subscribedTo.items': items}})

        success = True
        message = 'Permissions Reseted to contexts defaults'

    return dict(api=api,
                url='%s/maintenance' % api.getAppURL(),
                success=success,
                message=message)
