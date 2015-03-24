# -*- coding: utf-8 -*-
from max import maxlogger
from max.MADMax import MADMaxCollection
from pyramid.security import Allow, Authenticated
from max.exceptions import ObjectNotFound, Forbidden, UnknownUserError
from max.security import Manager, is_self_operation, Owner, is_manager, is_owner
from max.security import permissions
from max.rest.utils import getMaxModelByObjectType

import pkg_resources
import inspect


DUMMY_CLOUD_API_DATA = {
    "twitter": {
        "consumer_secret": "",
        "access_token": "",
        "consumer_key": "",
        "access_token_secret": ""
    }
}


def get_pyramid_authorization_frame():
    """
        Returns the upper frame if we determine that on this point,
        pyramid is checking the acls from the permits  method of the
        authorization module
    """

    frame = inspect.currentframe().f_back.f_back
    parent_method = frame.f_code.co_name
    parent_filename = frame.f_code.co_filename
    if parent_method == 'permits' and parent_filename.endswith('pyramid/authorization.py'):
        return frame


class Root(dict):
    __parent__ = __name__ = None

    @property
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.do_maintenance),
            (Allow, Manager, permissions.view_server_settings),
            (Allow, Manager, permissions.manage_security)
        ]

        # Grant the permission associated with the view to the authenticated user
        # ONLY when we're making a HEAD request. This way we can keep view permissions sane
        # Related to GET methods, while allowing HEAD counterpart available to the
        # requesting user
        if self.request.method == 'HEAD':
            frame = get_pyramid_authorization_frame()
            if frame:
                required_view_permission = frame.f_locals['permission']
                acl.append((Allow, self.request.authenticated_userid, required_view_permission))

        return acl

    def __init__(self, request):
        self.request = request
        self['contexts'] = ContextTraverser(self, request)
        self['people'] = PeopleTraverser(self, request)
        self['subscriptions'] = SubscriptionsTraverser(self, request)
        self['activities'] = ActivitiesTraverser(self, request)
        self['comments'] = CommentsTraverser(self, request)


class MongoDBTraverser(MADMaxCollection):

    collection_name = ''
    query_key = '_id'

    def __init__(self, parent, request):
        self.request = request
        self.__parent__ = parent
        self.collection = self.request.registry.max_store[self.collection_name]
        self.show_fields = None


class CommentsTraverser(object):
    """
        Traverser to hold permissons for global comment access

        This traverser will look for a comment inside an activty, assuming the parent
        object is an activity
    """
    def __init__(self, parent, request):
        self.request = request
        self.db = request.registry.max_store
        self.__parent__ = parent

    def __getitem__(self, key):
        from max.models import Activity

        if isinstance(self.__parent__, Activity):
            import ipdb;ipdb.set_trace()
            return

    @property
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.view_comments)
        ]
        return acl


class ContextTraverser(MongoDBTraverser):
    collection_name = 'contexts'
    query_key = 'hash'

    @property
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.add_context),
            (Allow, Manager, permissions.list_contexts),
            (Allow, Authenticated, permissions.list_public_contexts),
            (Allow, Manager, permissions.modify_context),
            (Allow, Manager, permissions.delete_context),
            (Allow, Manager, permissions.view_context),
            (Allow, Manager, permissions.view_context_activity),
            (Allow, Manager, permissions.view_subscriptions),
            (Allow, Owner, permissions.view_subscriptions)
        ]
        return acl


class ActivitiesTraverser(MongoDBTraverser):
    collection_name = 'activity'
    query_key = '_id'

    @property
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.view_activities),
        ]
        return acl


class PeopleTraverser(MongoDBTraverser):
    collection_name = 'users'
    query_key = 'username'

    def __getitem__(self, userid):
        """
            Overrides __getitem__ to avoid fetching the user twice , when
            user that we're going to request is the same actor on the request.

            Because the actor on the request won't be in the traversal chain,
            provide it a parent before returning.

            If the userid doesn't match the request actor fallback to query database.
            If the actor doesn't exists, raise a not found.
        """
        userid = userid.lower()
        if userid == self.request.actor_username:
            actor = self.request.actor
            if actor is None:
                raise UnknownUserError("Object with %s %s not found inside %s" % (self.query_key, userid, self.collection.name))
            actor.__parent__ = self
            return actor

        return MADMaxCollection.__getitem__(self, userid)

    @property
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.add_people),
            (Allow, Manager, permissions.list_visible_people),
            (Allow, Manager, permissions.modify_user),
            (Allow, Manager, permissions.delete_user),
            (Allow, Authenticated, permissions.list_visible_people),
            (Allow, Manager, permissions.view_subscriptions),
            (Allow, Owner, permissions.view_subscriptions),
        ]

        # Grant add permission if user is trying to create itself
        if self.request.authenticated_userid == self.request.actor_username:
            acl.append((Allow, self.request.authenticated_userid, permissions.add_people))

        return acl


class Subscription(dict):
    """
        Object representing a subscription.

        This is temporary, to allow us to work assuming subscriptions are
        real objects. In the (near) future, this should be migrated to models
        as a regular mongodb collecion object.
    """

    def get_subscription(self, context):
        """
            Retrieves the subscription
        """
        ContextClass = getMaxModelByObjectType(context['objectType'])
        temp_context = ContextClass()
        temp_context.fromObject(context)
        for subscription in self.actor.get(temp_context.user_subscription_storage, []):
            if subscription.get(temp_context.unique.lstrip('_')) == str(temp_context[temp_context.unique]):
                return subscription

        context['exists'] = False
        return context

    def __init__(self, parent, request, chash, actor):
        from max.models import Context
        self.__parent__ = parent
        self.request = request
        self.hash = chash
        self.actor = actor
        self.context = Context()
        self.context.fromObject({'objectType': 'context', 'hash': chash})
        subscription = self.get_subscription({'hash': chash, 'objectType': 'context'})

        # If a subscription is not found, we raise a Forbidden here, except that
        # the user authenticated is a Manager: in that case, a fake read-granted subscription is
        # given in order to grant him the view_activities on this subscription's context
        if not subscription.get('exists', True):
            current_user_is_manager = is_manager(self.request, self.request.authenticated_userid)
            if not current_user_is_manager:
                raise Forbidden('{} is not subscribed to {}'.format(self.request.actor_username, self.hash))
            subscription.update({'permissions': ['read']})

        self.update(subscription)

    @property
    def _owner(self):
        """
            Proxy of the ownership of the underliying context
        """
        try:
            return self.context._owner
        except:
            # XXX Maybe we want to raise this directly form wake or alreadyExists ???
            raise ObjectNotFound("There is no context with hash {}".format(self.hash))

    @property
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.add_activity),
            (Allow, Manager, permissions.view_activities),
        ]

        # Allow Owners and Managers to manage subscription permissions on real susbcriptions
        if self.get('exists', True) and (is_manager(self.request, self.request.authenticated_userid) or is_owner(self, self.request.authenticated_userid)):
            acl.append((Allow, self.request.authenticated_userid, permissions.manage_subcription_permissions))

        # Grant ubsubscribe permission if the user subscription allows it
        # but only if is trying to unsubscribe itself.
        if 'unsubscribe' in self.get('permissions', []) and is_self_operation(self.request):
            acl.append((Allow, self.request.authenticated_userid, permissions.remove_subscription))

        # Grant add_activity permission if the user subscription allows it
        # but only if is trying to post as himself. This avoids Context owners to create
        # activity impersonating othe users
        if 'write' in self.get('permissions', []) and is_self_operation(self.request):
            acl.append((Allow, self.request.authenticated_userid, permissions.add_activity))

        # Grant view_activities permission if the user subscription allows it
        if 'read' in self.get('permissions', []):
            acl.append((Allow, self.request.authenticated_userid, permissions.view_activities))

        return acl


class SubscriptionsTraverser(object):
    def __init__(self, parent, request):
        self.request = request
        self.db = request.registry.max_store
        self.__parent__ = parent

    def __getitem__(self, key):
        return Subscription(self, self.request, key, self.request.actor)

    @property
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.remove_subscription),
            (Allow, Owner, permissions.remove_subscription),
        ]

        return acl


def getMAXSettings(request):
    return request.registry.max_settings


def loadMAXSettings(settings):
    max_ini_settings = {key.replace('max.', 'max_'): settings[key] for key in settings.keys() if 'max' in key}
    max_ini_settings['max_message_defaults'] = {
        "source": "max",
        "domain": max_ini_settings.get('max_server_id', ''),
        "version": pkg_resources.require("max")[0].version,
    }
    return max_ini_settings


def loadCloudAPISettings(registry):
    cloudapis_settings = registry.max_store.cloudapis.find_one()
    if cloudapis_settings:
        return cloudapis_settings
    else:
        maxlogger.info("No cloudapis info found. Please run initialization database script.")  #pragma: no cover
        return DUMMY_CLOUD_API_DATA


def loadMAXSecurity(registry):
    security_settings = [a for a in registry.max_store.security.find({})]
    if security_settings:
        return security_settings[0]
    else:
        maxlogger.info("No security info found. Please run initialization database script.")  #pragma: no cover
