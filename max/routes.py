PUBLIC_RESOURCES = {
    'users': dict(route='/people', category='User', name='Users', traverse='/people'),
    'user': dict(route='/people/{username}', category='User', name='User', traverse='/people/{username}'),
    'avatar': dict(route='/people/{username}/avatar', filesystem=True, category='User', name='User avatar', traverse='/people/{username}'),
    'avatar_sizes': dict(route='/people/{username}/avatar/{size}', filesystem=True, category='User', name='User avatar sizes', traverse='/people/{username}'),
    'user_activities': dict(route='/people/{username}/activities', category='Activities', name='User activities', traverse='/people/{username}'),
    'user_device': dict(route='/people/{username}/device/{platform}/{token}', category='User', name='User device tokens', traverse='/people/{username}'),
    'user_platform_tokens': dict(route='/people/{username}/device/{platform}', category='User', name='User device tokens by platform', traverse='/people/{username}'),


    'activities': dict(route='/activities', category='Activities', name='Activities', traverse='/activities'),
    'comments': dict(route='/activities/comments', category='Comments', name='Comments (Global)', traverse='/comments'),
    'activity': dict(route='/activities/{activity}', category='Activities', name='Activity', traverse='/activities/{activity}'),
    'timeline': dict(route='/people/{username}/timeline', category='Activities', name='User Timeline'),
    'timeline_authors': dict(route='/people/{username}/timeline/authors', category='Activities', name='User Timeline authors'),
    'user_comments': dict(route='/people/{username}/comments', category='Comments', name='User comments', traverse='/people/{username}'),

    'activity_comments': dict(route='/activities/{activity}/comments', category='Comments', name='Activity comments', traverse="/activities/{activity}"),
    'activity_comment': dict(route='/activities/{activity}/comments/{comment}', category='Comments', name='Activity comment', traverse='/activities/{activity}/comments/{comment}'),

    'subscriptions': dict(route='/people/{username}/subscriptions', category='Subscriptions', name='User subscriptions', traverse='/people/{username}'),
    'subscription': dict(route='/people/{username}/subscriptions/{hash}', category='Subscriptions', name='User subscription'),

    'user_conversations': dict(route='/people/{username}/conversations', category='Conversations', name='User conversations', traverse='/conversations'),
    'user_conversation': dict(route='/people/{username}/conversations/{id}', category='Conversations', name='User conversation', traverse='/conversations/{id}'),
    'user_conversation_messages': dict(route='/people/{username}/conversations/{id}/messages', category='Conversations', name='User conversation messages'),

    'contexts': dict(route='/contexts', category='Contexts', name='Contexts', traverse='/contexts'),
    'context': dict(route='/contexts/{hash}', category='Contexts', name='Context', traverse='/contexts/{hash}'),
    'context_avatar': dict(route='/contexts/{hash}/avatar', filesystem=True, category='Contexts', name='Context avatar'),
    'public_contexts': dict(route='/contexts/public', category='Contexts', name='Public contexts', traverse='/contexts'),
    'context_user_permissions_defaults': dict(route='/contexts/{hash}/permissions/{username}/defaults', category='Contexts', name='Context permissions defaults', traverse='/contexts/{hash}'),
    'context_user_permission': dict(route='/contexts/{hash}/permissions/{username}/{permission}', category='Contexts', name='Context permission', traverse='/contexts/{hash}'),
    'context_activities': dict(route='/contexts/{hash}/activities', category='Activities', name='Context activities', traverse='/contexts/{hash}'),
    'context_push_tokens': dict(route='/contexts/{hash}/tokens', category='Contexts', name='Context tokens'),
    'context_comments': dict(route='/contexts/{hash}/comments', category='Comments', name='Context comments', traverse='/contexts/{hash}'),
    'context_activities_authors': dict(route='/contexts/{hash}/activities/authors', category='Activities', name='Context authors', traverse='/contexts/{hash}'),
    'context_subscriptions': dict(route='/contexts/{hash}/subscriptions', category='Contexts', name='Users subscribed to context', traverse='/contexts/{hash}'),
    'context_subscription': dict(route='/contexts/{hash}/subscriptions/{username}', category='Contexts', name='User subscription', traverse='/contexts/{hash}'),
    'context_tags': dict(route='/contexts/{hash}/tags', category='Contexts', name='Context tags', traverse='/contexts/{hash}'),
    'context_tag': dict(route='/contexts/{hash}/tags/{tag}', category='Contexts', name='Context tag', traverse='/contexts/{hash}'),

    # MAX 3.0
    'conversations': dict(route='/conversations', category='Conversations', name='Conversations', traverse='/conversations'),
    'conversation': dict(route='/conversations/{id}', category='Conversations', name='Conversation', traverse='/conversations/{id}'),
    'conversation_owner': dict(route='/conversations/{id}/owner', category='Conversations', name='Conversation owner', traverse='/conversations/{id}'),
    'conversation_avatar': dict(route='/conversations/{id}/avatar', filesystem=True, category='Conversations', name='Conversation avatar', traverse='/conversations/{id}'),
    'conversation_push_tokens': dict(route='/conversations/{id}/tokens', category='Conversations', name='Conversation tokens', traverse='/conversations/{id}'),
    'messages': dict(route='/conversations/{id}/messages', category='Conversations', name='Conversation mesages', traverse='/conversations/{id}'),
    'message': dict(route='/conversations/{id}/messages/{activity}', category='Conversations', name='Conversation message', traverse='/messages/{activity}'),
    'participants': dict(route='/conversations/{id}/participants', category='Conversations', name='Conversation participants', traverse='/conversations/{id}'),
    'participant': dict(route='/conversations/{id}/participants/{username}', category='Conversations', name='Conversation participant', traverse='/conversations/{id}'),

    # MAX 3.6
    'flag': dict(route='/activities/{activity}/flag', category='Activities', traverse='/activities/{activity}'),
    'likes': dict(route='/activities/{activity}/likes', category='Activities', traverse='/activities/{activity}'),
    'like': dict(route='/activities/{activity}/likes/{username}', category='Activities', traverse='/activities/{activity}'),
    'user_likes': dict(route='/people/{username}/likes', category='User', name='User liked activity'),
    'favorites': dict(route='/activities/{activity}/favorites', category='Activities', traverse='/activities/{activity}'),
    'favorite': dict(route='/activities/{activity}/favorites/{username}', category='Activities', traverse='/activities/{activity}'),
    'user_favorites': dict(route='/people/{username}/favorites', category='User', name='User favorited activities'),

    'activity_image': dict(route='/activities/{activity}/image', category='Activities', name='Image', traverse='/activities/{activity}'),
    'activity_image_sizes': dict(route='/activities/{activity}/image/{size}', category='Activities', name='Named size Image', traverse='/activities/{activity}'),
    'activity_file_download': dict(route='/activities/{activity}/file/download', category='Activities', name='File', traverse='/activities/{activity}'),

    'message_image': dict(route='/messages/{id}/image', category='Messages', name='Image', traverse='/messages/{activity}'),
    'message_image_sizes': dict(route='/messages/{id}/image/{size}', category='Messages', name='Named size Image', traverse='/messages/{activity}'),
    'message_file_download': dict(route='/messages/{id}/file/download', category='Messages', name='File', traverse='/messages/{activity}'),

    # MAX 4.0
    'user_shares': dict(route='/people/{username}/shares'),
    'follows': dict(route='/people/{username}/follows'),
    'follow': dict(route='/people/{username}/follows/{followedUsername}'),
    'shares': dict(route='/activities/{activity}/shares'),
    'share': dict(route='/activities/{activity}/shares/{shareId}'),

    # Not implemented / Not in roadmap
    'context_permissions': dict(route='/contexts/{hash}/permissions'),


}

INFO_RESOURCES = {
    'info': dict(route='/info', category='Management', name='Public settings'),
    'info_api': dict(route='/info/api', category='Management', name='Api endpoints definition'),
    'info_settings': dict(route='/info/settings', category='Management', name='Restricted settings'),
}

RESTRICTED_RESOURCES = {

    'admin_security': dict(route='/admin/security', category='Management', name='Security settings', traverse="/security"),
    'admin_security_role': dict(route='/admin/security/roles/{role}', category='Management', name='Role users', traverse="/security/"),
    'admin_security_role_user': dict(route='/admin/security/roles/{role}/users/{user}', category='Management', name='User role', traverse="/security/"),
    'admin_security_users': dict(route='/admin/security/users', category='Management', name='Users with security', traverse="/security/"),
    'maintenance_keywords': dict(route='/admin/maintenance/keywords', category='Management', name='Keywords maintenance'),
    'maintenance_dates': dict(route='/admin/maintenance/dates', category='Management', name='Dates maintenance'),
    'maintenance_subscriptions': dict(route='/admin/maintenance/subscriptions', category='Management', name='Subscriptions maintenance'),
    'maintenance_conversations': dict(route='/admin/maintenance/conversations', category='Management', name='Conversations maintenance'),
    'maintenance_users': dict(route='/admin/maintenance/users', category='Management', name='Users Maintenance'),
    'maintenance_exceptions': dict(route='/admin/maintenance/exceptions', category='Management', name='Error Exception list'),
    'maintenance_exception': dict(route='/admin/maintenance/exceptions/{hash}', category='Management', name='Error Exception'),
}

RESOURCES = {}
RESOURCES.update(PUBLIC_RESOURCES)
RESOURCES.update(RESTRICTED_RESOURCES)
RESOURCES.update(INFO_RESOURCES)
