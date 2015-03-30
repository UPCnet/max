# -*- coding: utf-8 -*-
from max import maxlogger
from max.MADMax import MADMaxCollection
from pyramid.security import Allow, Authenticated
from max.exceptions import ObjectNotFound, UnknownUserError
from max.security import Manager, Owner
from max.security import permissions
from pyramid.decorator import reify
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

    @reify
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
        self['activities'] = ActivitiesTraverser(self, request)
        self['comments'] = CommentsTraverser(self, request)
        self['conversations'] = ConversationsTraverser(self, request)
        self['messages'] = MessagesTraverser(self, request)


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
    def __init__(self, parent, request, activity=None):
        self.request = request
        self.db = request.registry.max_store
        self.__parent__ = parent
        self.activity = activity

    def __getitem__(self, commentid):
        from max.ASObjects import Comment

        if self.activity:
            comment = self.activity.get_comment(commentid)
            comment_object = Comment(comment, creating=False)
            comment_object.__parent__ = self
            return comment_object
        else:
            raise ObjectNotFound('Activity {} has no comment with id {}'.format(self.activity['_id'], commentid))

    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.list_comments)
        ]
        return acl


class ContextTraverser(MongoDBTraverser):
    collection_name = 'contexts'
    query_key = 'hash'

    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.add_context),
            (Allow, Manager, permissions.list_contexts),
            (Allow, Authenticated, permissions.list_public_contexts),
            (Allow, Manager, permissions.modify_context),
            (Allow, Manager, permissions.delete_context),
            (Allow, Manager, permissions.view_context),
            (Allow, Manager, permissions.list_activities),
            (Allow, Manager, permissions.view_subscriptions),
            (Allow, Owner, permissions.view_subscriptions)
        ]

        return acl


class ConversationsTraverser(MongoDBTraverser):
    collection_name = 'conversations'
    query_key = '_id'

    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.add_conversation),
            (Allow, Authenticated, permissions.list_conversations),
            (Allow, Authenticated, permissions.add_conversation),
            (Allow, Manager, permissions.add_conversation_for_others),
            (Allow, Manager, permissions.list_conversations_unsubscribed),
        ]

        return acl


class ActivitiesTraverser(MongoDBTraverser):
    collection_name = 'activity'
    query_key = '_id'

    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.list_activities),
        ]
        return acl


class MessagesTraverser(MongoDBTraverser):
    collection_name = 'messages'
    query_key = '_id'

    @reify
    def __acl__(self):
        acl = [
            (Allow, Manager, permissions.list_messages),
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

    @reify
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
