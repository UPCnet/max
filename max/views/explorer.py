# -*- coding: utf-8 -*-
from pyramid.view import view_config

from max.views.api import TemplateAPI
from max.rest.utils import findKeywords
from max.MADMax import MADMaxCollection


def getFieldByName(field, obj, default='--'):
    """
    """
    last = obj
    parts = field.split('.')
    for part in parts:
        last = last.get(part,None)
        if last == None:
            return default
    return last


@view_config(name="explorer", renderer='max:templates/explorer.pt', permission='restricted')
def explorerView(context, request):
    page_title = "MAX Server DB Explorer"
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

    user_cols = [dict(id="id", title="ID"),
                 dict(id="username", title="Nom d'usuari"),
                 dict(id="displayName", title="Nom Sencer"),
                ]

    activity_cols = [dict(id="id", title="ID"),
                     dict(id="object.objectType", title="Tipus"),
                     dict(id="verb", title="Acció"),
                ]

    context_cols = [dict(id="id", title="ID"),
                   dict(id="displayName", title="Nom"),
                   dict(id="url", title="URL"),
                   ]

    user_cols_ids = [a['id'] for a in user_cols]
    activity_cols_ids = [a['id'] for a in activity_cols]
    context_cols_ids = [a['id'] for a in context_cols]

    users_dump = MADMaxCollection(context.db.users).dump(flatten=True)[:10]
    activities_dump = MADMaxCollection(context.db.activity).dump(flatten=True)[:10]
    contexts_dump = MADMaxCollection(context.db.contexts).dump(flatten=True)[:10]

    user_data = [[dict(id=field, value=getFieldByName(field,entry)) for field in user_cols_ids] for entry in users_dump]
    activity_data = [[dict(id=field, value=getFieldByName(field,entry)) for field in activity_cols_ids] for entry in activities_dump]
    context_data = [[dict(id=field, value=getFieldByName(field,entry))  for field in context_cols_ids] for entry in contexts_dump]

    collections = [dict(id="users", title="Usuaris", data=user_data, icon="user", cols=user_cols),
                   dict(id="activities", title="Activitats", data=activity_data, icon="star", cols=activity_cols),
                   dict(id="contexts", title="Contextes", data=context_data, icon="leaf", cols=context_cols),
                  ]

    return dict(api=api,
                url='%s/explorer' % api.getAppURL(),
                success=success,
                message=message,
                db=collections,
                )
