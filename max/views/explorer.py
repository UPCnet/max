# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPOk

from max.views.api import TemplateAPI
from max.MADMax import MADMaxCollection

import requests
import json


def getFieldByName(field, obj, default='--'):
    """
    """
    last = obj
    parts = field.split('.')
    for part in parts:
        last = last.get(part, None)
        if last == None:
            return default
    return last


@view_config(name="addNew", permission='restricted')
def addNew(context, request):
    api = TemplateAPI(context, request)
    objectType = request.params.get('type', None)
    if objectType in ['context', 'user', 'activity']:
        if objectType == 'context':
            data = dict(
                      url=request.params.get('url'),
                      displayName=request.params.get('displayName'),
                      twitterHashtag=request.params.get('twitterHashtag'),
                      twitterUsername=request.params.get('twitterUsername'),
                      permissions=dict(read=request.params.get('read', 'public'), write=request.params.get('write', 'public')),
                   )
            req = requests.post('%s/contexts' % api.getAppURL(), data=json.dumps(data), auth=('operations', 'operations'))

        if objectType == 'user':
            data = dict(
                      displayName=request.params.get('displayName'),
                   )
            req = requests.post('%s/people/%s' % (api.getAppURL(), request.params.get('username')), data=json.dumps(data), auth=('operations', 'operations'))

        if req.status_code in [200, 201]:
            return HTTPOk()
        else:
            return HTTPBadRequest()
    else:
        return HTTPBadRequest()


@view_config(name="deleteObject", permission='restricted')
def delObj(context, request):
    objectType = request.params.get('type', None)
    if objectType in ['context', 'user', 'activity']:
        objectId = request.params.get('objectId', None)
        if objectId:
            dbmap = dict(user='users', context='contexts', activity='activity')
            collection = MADMaxCollection(getattr(context.db, dbmap[objectType]))
            collection[objectId].delete()
            return HTTPOk()
        else:
            return HTTPBadRequest()
    else:
        return HTTPBadRequest()


@view_config(name="explorer", renderer='max:templates/explorer.pt', permission='restricted')
def explorerView(context, request):
    page_title = "MAX Server DB Explorer"
    api = TemplateAPI(context, request, page_title)
    success = False
    message = ''
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

    collections = [dict(id="users", objectType='user', title="Usuaris", data=user_data, icon="user", cols=user_cols),
                   dict(id="activities", objectType='activity', title="Activitats", data=activity_data, icon="star", cols=activity_cols),
                   dict(id="contexts", objectType='context', title="Contextes", data=context_data, icon="leaf", cols=context_cols),
                  ]

    return dict(api=api,
                url='%s/explorer' % api.getAppURL(),
                success=success,
                message=message,
                db=collections,
                )
