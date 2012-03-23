from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented, HTTPNoContent
from pyramid.response import Response

from max.MADMax import MADMaxDB, MADMaxCollection
from max.models import Context
from max.decorators import MaxRequest, MaxResponse
from max.exceptions import InvalidPermission, Unauthorized, ObjectNotFound
from max.rest.ResourceHandlers import JSONResourceRoot, JSONResourceEntity
import os

from max.oauth2 import oauth2
from max.rest.utils import extractPostData


@view_config(route_name='contexts', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getContexts(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    contexts = mmdb.contexts.dump(flatten=1)
    handler = JSONResourceRoot(contexts)
    return handler.buildResponse()


@view_config(route_name='context', request_method='GET', permission='operations')
@MaxResponse
@MaxRequest
def getContext(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    urlhash = request.matchdict.get('urlHash', None)
    found_context = mmdb.contexts.getItemsByurlHash(urlhash)

    if not found_context:
        raise ObjectNotFound, "There's no context matching this url hash: %s" % urlhash

    handler = JSONResourceEntity(found_context[0].flatten())
    return handler.buildResponse()


@view_config(route_name='contexts', request_method='POST', permission='operations')
@MaxResponse
@MaxRequest
def addContext(context, request):
    """
    """
    # Initialize a Context object from the request
    newcontext = Context(request)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newcontext.get('_id'):
        # Already Exists
        code = 200
    else:
        # New User
        code = 201
        contextid = newcontext.insert()
        newcontext['_id'] = contextid

    handler = JSONResourceEntity(newcontext.flatten(), status_code=code)
    return handler.buildResponse()


@view_config(route_name='context', request_method='PUT', permission='operations')
@MaxResponse
@MaxRequest
def ModifyContext(context, request):
    """
    """
    urlHash = request.matchdict['urlHash']
    contexts = MADMaxCollection(context.db.contexts)
    maxcontext = contexts.getItemsByurlHash(urlHash)
    if maxcontext:
        maxcontext = maxcontext[0]
    else:
        raise ObjectNotFound, 'Unknown context: %s' % urlHash

    params = extractPostData(request)
    allowed_fields = [fieldName for fieldName in maxcontext.schema if maxcontext.schema[fieldName].get('operations_mutable', 0)]
    properties = {fieldName: params.get(fieldName) for fieldName in allowed_fields if params.get(fieldName, None)}

    maxcontext.modifyContext(properties)

    maxcontext = contexts.getItemsByurlHash(urlHash)[0]
    handler = JSONResourceEntity(maxcontext.flatten())
    return handler.buildResponse()


@view_config(route_name='context', request_method='DELETE', permission='operations')
@MaxResponse
@MaxRequest
def DeleteContext(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    urlhash = request.matchdict.get('urlHash', None)
    found_context = mmdb.contexts.getItemsByurlHash(urlhash)

    if not found_context:
        raise ObjectNotFound, "There's no context matching this url hash: %s" % urlhash

    found_context[0].delete()
    found_context[0].removeUserSubscriptions()
    return HTTPNoContent()


@view_config(route_name='context_user_permission', request_method='PUT', permission='operations')
@MaxResponse
@MaxRequest
def grantPermissionOnContext(context, request):
    """
    """
    permission = request.matchdict.get('permission', None)
    if permission not in ['read', 'write', 'join', 'invite']:
        raise InvalidPermission, "There's not any permission named '%s'" % permission

    urlhash = request.matchdict.get('urlHash', None)
    subscription = None
    pointer = 0
    while subscription == None and pointer < len(request.actor.subscribedTo['items']):
        if request.actor.subscribedTo['items'][pointer]['urlHash'] == urlhash:
            subscription = request.actor.subscribedTo['items'][pointer]
        pointer += 1

    if not subscription:
        raise Unauthorized, "You can't set permissions on a context where you are not subscribed"

    #If we reach here, we are subscribed to a context and ready to set the permission

    permissions = subscription['permissions']
    if permission in permissions:
        #Already have the permission
        code = 200
    else:
        #Assign the permission
        code = 201
        request.actor.grantPermission(subscription, permission)
        permissions.append(permission)

    handler = JSONResourceEntity(subscription, status_code=code)
    return handler.buildResponse()


@view_config(route_name='context_user_permission', request_method='DELETE', permission='operations')
@MaxResponse
@MaxRequest
def revokePermissionOnContext(context, request):
    """
    """
    permission = request.matchdict.get('permission', None)
    if permission not in ['read', 'write', 'join', 'invite']:
        raise InvalidPermission, "There's not any permission named '%s'" % permission

    urlhash = request.matchdict.get('urlHash', None)
    subscription = None
    pointer = 0
    while subscription == None and pointer < len(request.actor.subscribedTo['items']):
        if request.actor.subscribedTo['items'][pointer]['urlHash'] == urlhash:
            subscription = request.actor.subscribedTo['items'][pointer]
        pointer += 1

    if not subscription:
        raise Unauthorized, "You can't rempve permissions on a context where you are not subscribed"

    #If we reach here, we are subscribed to a context and ready to remove the permission

    code = 200
    permissions = subscription['permissions']
    if permission in permissions:
        #We have the permission, let's delete it
        request.actor.revokePermission(subscription, permission)
        subscription['permissions'] = [a for a in permissions if permission != a]

    handler = JSONResourceEntity(subscription, status_code=code)
    return handler.buildResponse()
