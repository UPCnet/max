from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotImplemented
from pyramid.response import Response

from max.MADMax import MADMaxDB, MADMaxCollection
from max.models import Context
from max.decorators import MaxRequest, MaxResponse
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


@view_config(route_name='context', request_method='GET')
@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getContext(context, request):
    """
    """
    return HTTPNotImplemented()


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
#@MaxResponse
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


@view_config(route_name='context', request_method='DELETE')
def DeleteContext(context, request):
    """
    """
    return HTTPNotImplemented()
