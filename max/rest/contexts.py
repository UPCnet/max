# -*- coding: utf-8 -*-
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent
from pyramid.response import Response

from max.MADMax import MADMaxDB, MADMaxCollection
from max.models import Context
from max.decorators import MaxRequest, MaxResponse
from max.exceptions import InvalidPermission, Unauthorized, ObjectNotFound
from max.rest.ResourceHandlers import JSONResourceEntity
import os

from max.rest.utils import downloadTwitterUserImage
import time


@view_config(route_name='context', request_method='GET', permission='operations')
@MaxResponse
@MaxRequest
def getContext(context, request):
    """
        /contexts/{hash}

        Return a context by its hash.
    """
    mmdb = MADMaxDB(context.db)
    chash = request.matchdict.get('hash', None)
    found_context = mmdb.contexts.getItemsByhash(chash)

    if not found_context:
        raise ObjectNotFound("There's no context matching this url hash: %s" % chash)

    handler = JSONResourceEntity(found_context[0].flatten())
    return handler.buildResponse()


@view_config(route_name='context_avatar', request_method='GET')
def getContextAvatar(context, request):
    """
        /contexts/{hash}/avatar

        Return the context's avatar. To the date, this is only implemented to
        work integrated with Twitter.
    """
    chash = request.matchdict['hash']
    AVATAR_FOLDER = request.registry.settings.get('avatar_folder')
    context_image_filename = '%s/%s.jpg' % (AVATAR_FOLDER, chash)

    if not os.path.exists(context_image_filename):
        mmdb = MADMaxDB(context.db)
        found_context = mmdb.contexts.getItemsByhash(chash)
        if len(found_context) > 0:
            twitter_username = found_context[0]['twitterUsername']
            downloadTwitterUserImage(twitter_username, context_image_filename)

    if os.path.exists(context_image_filename):
        # Calculate time since last download and set if we have to redownload or not
        modification_time = os.path.getmtime(context_image_filename)
        hours_since_last_modification = (time.time() - modification_time) / 60 / 60
        if hours_since_last_modification > 3:
            mmdb = MADMaxDB(context.db)
            found_context = mmdb.contexts.getItemsByhash(chash)
            twitter_username = found_context[0]['twitterUsername']
            downloadTwitterUserImage(twitter_username, context_image_filename)
    else:
        context_image_filename = '%s/missing.jpg' % (AVATAR_FOLDER)

    data = open(context_image_filename).read()
    image = Response(data, status_int=200)
    image.content_type = 'image/jpeg'
    return image


@view_config(route_name='contexts', request_method='POST', permission='operations')
@MaxResponse
@MaxRequest
def addContext(context, request):
    """
        /contexts

        Adds a context.
    """
    # Initialize a Context object from the request
    newcontext = Context()
    newcontext.fromRequest(request)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newcontext.get('_id'):
        # Already Exists
        code = 200
    else:
        # New context
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
        /contexts/{hash}

        Modify the given context.
    """
    chash = request.matchdict['hash']
    contexts = MADMaxCollection(context.db.contexts)
    maxcontext = contexts.getItemsByhash(chash)
    if maxcontext:
        maxcontext = maxcontext[0]
    else:
        raise ObjectNotFound('Unknown context: %s' % chash)

    properties = maxcontext.getMutablePropertiesFromRequest(request)
    maxcontext.modifyContext(properties)
    maxcontext.updateUsersSubscriptions()
    handler = JSONResourceEntity(maxcontext.flatten())
    return handler.buildResponse()


@view_config(route_name='context', request_method='DELETE', permission='operations')
@MaxResponse
@MaxRequest
def DeleteContext(context, request):
    """
    """
    mmdb = MADMaxDB(context.db)
    chash = request.matchdict.get('hash', None)
    found_context = mmdb.contexts.getItemsByhash(chash)

    if not found_context:
        raise ObjectNotFound("There's no context matching this url hash: %s" % chash)

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
        raise InvalidPermission("There's not any permission named '%s'" % permission)

    chash = request.matchdict.get('hash', None)
    subscription = None
    pointer = 0
    while subscription is None and pointer < len(request.actor.subscribedTo['items']):
        if request.actor.subscribedTo['items'][pointer]['hash'] == chash:
            subscription = request.actor.subscribedTo['items'][pointer]
        pointer += 1

    if not subscription:
        raise Unauthorized("You can't set permissions on a context where you are not subscribed")

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
        raise InvalidPermission("There's not any permission named '%s'" % permission)

    chash = request.matchdict.get('hash', None)
    subscription = None
    pointer = 0
    while subscription is None and pointer < len(request.actor.subscribedTo['items']):
        if request.actor.subscribedTo['items'][pointer]['hash'] == chash:
            subscription = request.actor.subscribedTo['items'][pointer]
        pointer += 1

    if not subscription:
        raise Unauthorized("You can't remove permissions on a context where you are not subscribed")

    #If we reach here, we are subscribed to a context and ready to remove the permission

    code = 200
    permissions = subscription['permissions']
    if permission in permissions:
        #We have the permission, let's delete it
        request.actor.revokePermission(subscription, permission)
        subscription['permissions'] = [a for a in permissions if permission != a]

    handler = JSONResourceEntity(subscription, status_code=code)
    return handler.buildResponse()
