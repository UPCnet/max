# -*- coding: utf-8 -*-
"""
    Definitions of routes used on the api endpoints.

    This routes are loaded on application initialization, and its parameters
    used to configure the route as it's added.

    The routes have one required paramter "route" that defines the URI that will
    be used by pyramid router to match views with.

    There is a "traverse" parameter that if present, will be used to tell pyramid
    which object should try to traverse to be the context of a request. URI's used in
    this parameter don't have to match URI in "route" param, but they must conform to
    existing Traversers on the Root context. see max.resources for more info. Routes
    defined without "traverse", will have the Root context as the request context.

    Finally there are keys used in the api info endpoint to classify the endpoints.
    Routes in this file are sorted by the kind of traverser used. "category"
    parameter defines a classification based on a more 'high level' view of the endpoint.
    For example "subcriptions" resource is classified on "Subscriptions" even if it's
    using the people traverser, in order to group it with all other subscription related endpoints.

    IMPORTANT! Routes with fixed path segments, that must override routes with the same pattern but
    with dynamic segments, must be defined earlier, if not, pyramid router will match the dynamic one first.
    For example, /activities/comments must be defined earlier that /activities/{activityid}.
"""

from collections import OrderedDict

RESOURCES = OrderedDict()

RESOURCES['users'] = dict(route='/people', category='User', name='Users', traverse='/people', actor_not_required=['POST'])
RESOURCES['user'] = dict(route='/people/{username}', category='User', name='User', traverse='/people/{username}')
RESOURCES['avatar'] = dict(route='/people/{username}/avatar', filesystem=True, category='User', name='User avatar', traverse='/people/{username}')
RESOURCES['avatar_sizes'] = dict(route='/people/{username}/avatar/{size}', filesystem=True, category='User', name='User avatar sizes', traverse='/people/{username}')
RESOURCES['user_activities'] = dict(route='/people/{username}/activities', category='Activities', name='User activities', traverse='/people/{username}')
RESOURCES['timeline'] = dict(route='/people/{username}/timeline', category='Activities', name='User Timeline', traverse='/people/{username}')
RESOURCES['timeline_authors'] = dict(route='/people/{username}/timeline/authors', category='Activities', name='User Timeline authors', traverse='/people/{username}')
RESOURCES['user_comments'] = dict(route='/people/{username}/comments', category='Comments', name='User comments', traverse='/people/{username}')
RESOURCES['subscriptions'] = dict(route='/people/{username}/subscriptions', category='Subscriptions', name='User subscriptions', traverse='/people/{username}')
RESOURCES['user_tokens'] = dict(route='/people/{username}/tokens', category='Tokens', name='User device tokens', traverse='/people/{username}')
RESOURCES['user_platform_tokens'] = dict(route='/people/{username}/tokens/platforms/{platform}', category='Tokens', name='User device tokens by platform', traverse='/people/{username}')

RESOURCES['tokens'] = dict(route='/tokens', category='Tokens', name='Device tokens', traverse='/tokens')
RESOURCES['token'] = dict(route='/tokens/{token}', category='Tokens', name='Device token', traverse='/tokens/{token}')
RESOURCES['context_push_tokens'] = dict(route='/contexts/{hash}/tokens', category='Tokens', name='Context tokens', traverse='/tokens')
RESOURCES['conversation_push_tokens'] = dict(route='/conversations/{id}/tokens', category='Tokens', name='Conversation tokens', traverse='/tokens')

RESOURCES['comments'] = dict(route='/activities/comments', category='Comments', name='Comments (Global)', traverse='/comments')

RESOURCES['activities'] = dict(route='/activities', category='Activities', name='Activities', traverse='/activities')
RESOURCES['activity'] = dict(route='/activities/{activity}', category='Activities', name='Activity', traverse='/activities/{activity}')
RESOURCES['activity_comments'] = dict(route='/activities/{activity}/comments', category='Comments', name='Activity comments', traverse="/activities/{activity}")
RESOURCES['activity_comment'] = dict(route='/activities/{activity}/comments/{comment}', category='Comments', name='Activity comment', traverse='/activities/{activity}/comments/{comment}')
RESOURCES['flag'] = dict(route='/activities/{activity}/flag', category='Activities', traverse='/activities/{activity}')
RESOURCES['likes'] = dict(route='/activities/{activity}/likes', category='Activities', traverse='/activities/{activity}')
RESOURCES['like'] = dict(route='/activities/{activity}/likes/{username}', category='Activities', traverse='/activities/{activity}')
RESOURCES['favorites'] = dict(route='/activities/{activity}/favorites', category='Activities', traverse='/activities/{activity}')
RESOURCES['favorite'] = dict(route='/activities/{activity}/favorites/{username}', category='Activities', traverse='/activities/{activity}')
RESOURCES['activity_image'] = dict(route='/activities/{activity}/image', category='Activities', name='Image', traverse='/activities/{activity}')
RESOURCES['activity_image_sizes'] = dict(route='/activities/{activity}/image/{size}', category='Activities', name='Named size Image', traverse='/activities/{activity}')
RESOURCES['activity_file_download'] = dict(route='/activities/{activity}/file/download', category='Activities', name='File', traverse='/activities/{activity}')

RESOURCES['contexts'] = dict(route='/contexts', category='Contexts', name='Contexts', traverse='/contexts')
RESOURCES['public_contexts'] = dict(route='/contexts/public', category='Contexts', name='Public contexts', traverse='/contexts')
RESOURCES['context'] = dict(route='/contexts/{hash}', category='Contexts', name='Context', traverse='/contexts/{hash}')
RESOURCES['context_avatar'] = dict(route='/contexts/{hash}/avatar', filesystem=True, category='Contexts', name='Context avatar', traverse='/contexts/{hash}')
RESOURCES['context_user_permissions_defaults'] = dict(route='/contexts/{hash}/permissions/{username}/defaults', category='Contexts', name='Context permissions defaults', traverse='/contexts/{hash}')
RESOURCES['context_user_permission'] = dict(route='/contexts/{hash}/permissions/{username}/{permission}', category='Contexts', name='Context permission', traverse='/contexts/{hash}')
RESOURCES['context_activities'] = dict(route='/contexts/{hash}/activities', category='Activities', name='Context activities', traverse='/contexts/{hash}')
RESOURCES['context_comments'] = dict(route='/contexts/{hash}/comments', category='Comments', name='Context comments', traverse='/contexts/{hash}')
RESOURCES['context_activities_authors'] = dict(route='/contexts/{hash}/activities/authors', category='Activities', name='Context authors', traverse='/contexts/{hash}')
RESOURCES['context_subscriptions'] = dict(route='/contexts/{hash}/subscriptions', category='Contexts', name='Users subscribed to context', traverse='/contexts/{hash}')
RESOURCES['context_subscription'] = dict(route='/contexts/{hash}/subscriptions/{username}', category='Contexts', name='User subscription', traverse='/contexts/{hash}')
RESOURCES['context_tags'] = dict(route='/contexts/{hash}/tags', category='Contexts', name='Context tags', traverse='/contexts/{hash}')
RESOURCES['context_tag'] = dict(route='/contexts/{hash}/tags/{tag}', category='Contexts', name='Context tag', traverse='/contexts/{hash}')

RESOURCES['conversations'] = dict(route='/conversations', category='Conversations', name='Conversations', traverse='/conversations')
RESOURCES['conversation'] = dict(route='/conversations/{id}', category='Conversations', name='Conversation', traverse='/conversations/{id}')
RESOURCES['conversation_owner'] = dict(route='/conversations/{id}/owner', category='Conversations', name='Conversation owner', traverse='/conversations/{id}')
RESOURCES['conversation_avatar'] = dict(route='/conversations/{id}/avatar', filesystem=True, category='Conversations', name='Conversation avatar', traverse='/conversations/{id}')
RESOURCES['user_conversation'] = dict(route='/people/{username}/conversations/{id}', category='Conversations', name='User conversation', traverse='/conversations/{id}')
RESOURCES['participants'] = dict(route='/conversations/{id}/participants', category='Conversations', name='Conversation participants', traverse='/conversations/{id}')
RESOURCES['participant'] = dict(route='/conversations/{id}/participants/{username}', category='Conversations', name='Conversation participant', traverse='/conversations/{id}')

# This two resources share the same implementation. The latter is keeped to avoid setting a GET depreaction wrapper
RESOURCES['messages'] = dict(route='/conversations/{id}/messages', category='Conversations', name='Conversation mesages', traverse='/conversations/{id}')
RESOURCES['user_conversation_messages'] = dict(route='/people/{username}/conversations/{id}/messages', category='Conversations', name='User conversation messages', traverse='/conversations/{id}')

RESOURCES['message_image'] = dict(route='/messages/{id}/image', category='Messages', name='Image', traverse='/messages')
RESOURCES['message_image'] = dict(route='/messages/{id}/image', category='Messages', name='Image', traverse='/messages/{id}')
RESOURCES['message_image_sizes'] = dict(route='/messages/{id}/image/{size}', category='Messages', name='Named size Image', traverse='/messages/{id}')
RESOURCES['message_file_download'] = dict(route='/messages/{id}/file/download', category='Messages', name='File', traverse='/messages/{id}')

# Information resources

RESOURCES['info'] = dict(route='/info', category='Management', name='Public settings')
RESOURCES['info_api'] = dict(route='/info/api', category='Management', name='Api endpoints definition')
RESOURCES['info_settings'] = dict(route='/info/settings', category='Management', name='Restricted settings')

# Maintenance Resources

RESOURCES['admin_security'] = dict(route='/admin/security', category='Management', name='Security settings', traverse="/security", actor_not_required=['GET'])
RESOURCES['admin_security_role_user'] = dict(route='/admin/security/roles/{role}/users/{user}', category='Management', name='User role', traverse="/security/", actor_not_required=['GET', 'POST', 'DELETE'])
RESOURCES['admin_security_users'] = dict(route='/admin/security/users', category='Management', name='Users with security', traverse="/security/", actor_not_required=['GET'])
RESOURCES['maintenance_keywords'] = dict(route='/admin/maintenance/keywords', category='Management', name='Keywords maintenance', actor_not_required=['POST'])
RESOURCES['maintenance_dates'] = dict(route='/admin/maintenance/dates', category='Management', name='Dates maintenance', actor_not_required=['POST'])
RESOURCES['maintenance_subscriptions'] = dict(route='/admin/maintenance/subscriptions', category='Management', name='Subscriptions maintenance', actor_not_required=['POST'])
RESOURCES['maintenance_conversations'] = dict(route='/admin/maintenance/conversations', category='Management', name='Conversations maintenance', actor_not_required=['POST'])
RESOURCES['maintenance_users'] = dict(route='/admin/maintenance/users', category='Management', name='Users Maintenance', actor_not_required=['POST'])
RESOURCES['maintenance_tokens'] = dict(route='/admin/maintenance/tokens', category='Management', name='Tokens Maintenance', actor_not_required=['POST'])
RESOURCES['maintenance_exceptions'] = dict(route='/admin/maintenance/exceptions', category='Management', name='Error Exception list', actor_not_required=['GET'])
RESOURCES['maintenance_exception'] = dict(route='/admin/maintenance/exceptions/{hash}', category='Management', name='Error Exception', actor_not_required=['GET'])

# Routes not currently implemented

# RESOURCES['context_permissions'] = dict(route='/contexts/{hash}/permissions')
# RESOURCES['message'] = dict(route='/conversations/{id}/messages/{activity}')
# RESOURCES['admin_security_role'] = dict(route='/admin/security/roles/{role}')
# RESOURCES['subscription'] = dict(route='/people/{username}/subscriptions/{hash}')
# RESOURCES['user_likes'] = dict(route='/people/{username}/likes')
# RESOURCES['user_shares'] = dict(route='/people/{username}/shares')
# RESOURCES['follows'] = dict(route='/people/{username}/follows')
# RESOURCES['follow'] = dict(route='/people/{username}/follows/{followedUsername}')
# RESOURCES['shares'] = dict(route='/activities/{activity}/shares')
# RESOURCES['share'] = dict(route='/activities/{activity}/shares/{shareId}')
# RESOURCES['user_favorites'] = dict(route='/people/{username}/favorites')


# Deprecated routes

# RESOURCES['user_conversations'] = dict(route='/people/{username}/conversations', category='Conversations', name='User conversations', traverse='/conversations')
#
