PUBLIC_RESOURCES = {
    'users': {'route': '/people', 'category': 'User', 'name': 'Users'},
    'user': {'route': '/people/{username}', 'category': 'User', 'name': 'User'},
    'avatar': {'route': '/people/{username}/avatar', 'filesystem': True, 'category': 'User', 'name': 'User avatar'},
    'avatar_sizes': {'route': '/people/{username}/avatar/{size}', 'filesystem': True, 'category': 'User', 'name': 'User avatar sizes'},
    'user_activities': {'route': '/people/{username}/activities', 'category': 'Activities', 'name': 'User activities'},
    'user_device': {'route': '/people/{username}/device/{platform}/{token}', 'category': 'User', 'name': 'User device tokens'},

    'activities': {'route': '/activities', 'category': 'Activities', 'name': 'Activities'},
    'comments': {'route': '/activities/comments', 'category': 'Comments', 'name': 'Comments (Global)'},
    'activity': {'route': '/activities/{activity}', 'category': 'Activities', 'name': 'Activity'},
    'timeline': {'route': '/people/{username}/timeline', 'category': 'Activities', 'name': 'User Timeline'},
    'timeline_authors': {'route': '/people/{username}/timeline/authors', 'category': 'Activities', 'name': 'User Timeline authors'},

    'activity_comments': {'route': '/activities/{activity}/comments', 'category': 'Comments', 'name': 'Activity comments'},
    'activity_comment': {'route': '/activities/{activity}/comments/{comment}', 'category': 'Comments', 'name': 'Activity comment'},

    'subscriptions': {'route': '/people/{username}/subscriptions', 'category': 'Subscriptions', 'name': 'User subscriptions'},
    'subscription': {'route': '/people/{username}/subscriptions/{hash}', 'category': 'Subscriptions', 'name': 'User subscription'},

    'user_conversations': {'route': '/people/{username}/conversations', 'category': 'Conversations', 'name': 'User conversations'},
    'user_conversation': {'route': '/people/{username}/conversations/{id}', 'category': 'Conversations', 'name': 'User conversation'},
    'user_conversation_messages': {'route': '/people/{username}/conversations/{id}/messages', 'category': 'Conversations', 'name': 'User conversation messages'},

    'contexts': {'route': '/contexts', 'category': 'Contexts', 'name': 'Contexts'},
    'context': {'route': '/contexts/{hash}', 'category': 'Contexts', 'name': 'Context'},
    'context_avatar': {'route': '/contexts/{hash}/avatar', 'filesystem': True, 'category': 'Contexts', 'name': 'Context avatar'},
    'public_contexts': {'route': '/contexts/public', 'category': 'Contexts', 'name': 'Public contexts'},
    'context_user_permissions_defaults': {'route': '/contexts/{hash}/permissions/{username}/defaults', 'category': 'Contexts', 'name': 'Context permissions defaults'},
    'context_user_permission': {'route': '/contexts/{hash}/permissions/{username}/{permission}', 'category': 'Contexts', 'name': 'Context permission'},
    'context_activities': {'route': '/contexts/{hash}/activities', 'category': 'Activities', 'name': 'Context activities'},
    'context_push_tokens': {'route': '/contexts/{hash}/tokens', 'category': 'Contexts', 'name': 'Context tokens'},
    'context_comments': {'route': '/contexts/{hash}/comments', 'category': 'Comments', 'name': 'Context comments'},
    'context_activities_authors': {'route': '/contexts/{hash}/activities/authors', 'category': 'Activities', 'name': 'Context authors'},
    'context_subscriptions': {'route': '/contexts/{hash}/subscriptions', 'category': 'Contexts', 'name': 'Users subscribed to context'},
    'context_tags': {'route': '/contexts/{hash}/tags', 'category': 'Contexts', 'name': 'Context tags'},
    'context_tag': {'route': '/contexts/{hash}/tags/{tag}', 'category': 'Contexts', 'name': 'Context tag'},

    # MAX 3.0
    'conversations': {'route': '/conversations', 'category': 'Conversations', 'name': 'Conversations'},
    'conversation': {'route': '/conversations/{id}', 'category': 'Conversations', 'name': 'Conversation'},
    'conversation_owner': {'route': '/conversations/{id}/owner', 'category': 'Conversations', 'name': 'Conversation owner'},
    'conversation_avatar': {'route': '/conversations/{id}/avatar', 'filesystem': True, 'category': 'Conversations', 'name': 'Conversation avatar'},
    'pushtokens': {'route': '/conversations/{id}/tokens', 'category': 'Conversations', 'name': 'Conversation tokens'},
    'messages': {'route': '/conversations/{id}/messages', 'category': 'Conversations', 'name': 'Conversation mesages'},
    'message': {'route': '/conversations/{id}/messages/{activity}', 'category': 'Conversations', 'name': 'Conversation message'},
    'participants': {'route': '/conversations/{id}/participants', 'category': 'Conversations', 'name': 'Conversation participants'},
    'participant': {'route': '/conversations/{id}/participant', 'category': 'Conversations', 'name': 'Conversation participant'},

    # MAX 3.6
    'likes': {'route': '/activities/{activity}/likes', 'category': 'Activities'},
    'like': {'route': '/activities/{activity}/likes/{username}', 'category': 'Activities'},
    'user_likes': {'route': '/people/{username}/likes', 'category': 'User', 'name': 'User liked activity'},
    'favorites': {'route': '/activities/{activity}/favorites', 'category': 'Activities'},
    'favorite': {'route': '/activities/{activity}/favorites/{username}', 'category': 'Activities'},
    'user_favorites': {'route': '/people/{username}/favorites', 'category': 'User', 'name': 'User favorited activities'},

    'activity_image': {'route': '/activities/{activity}/image', 'category': 'Activities'},
    'activity_image_sizes': {'route': '/activities/{activity}/image/{size}', 'category': 'Activities'},
    'activity_file_download': {'route': '/activities/{activity}/file/download', 'category': 'Activities'},

    'message_image': {'route': '/messages/{id}/image', 'category': 'Messages'},
    'message_image_sizes': {'route': '/messages/{id}/image/{size}', 'category': 'Messages'},
    'message_file_download': {'route': '/messages/{id}/file/download', 'category': 'Messages'},

    # MAX 4.0
    'user_shares': {'route': '/people/{username}/shares'},
    'follows': {'route': '/people/{username}/follows'},
    'follow': {'route': '/people/{username}/follows/{followedUsername}'},
    'shares': {'route': '/activities/{activity}/shares'},
    'share': {'route': '/activities/{activity}/shares/{shareId}'},

    # Not implemented / Not in roadmap
    'user_comments': {'route': '/people/{username}/comments'},
    'user_conversations': {'route': '/people/{username}/conversations'},
    'context_permissions': {'route': '/contexts/{hash}/permissions'},
    'context_user_permissions': {'route': '/contexts/{hash}/permissions/{username}'},

}

INFO_RESOURCES = {
    'info': {'route': '/info', 'category': 'Management'},
    'info_api': {'route': '/info/api', 'category': 'Management'},
    'info_settings': {'route': '/info/settings', 'category': 'Management'},
}

RESTRICTED_RESOURCES = {

    'admin_security': {'route': '/admin/security', 'category': 'Management'},
    'admin_security_role': {'route': '/admin/security/roles/{role}', 'category': 'Management'},
    'admin_security_role_user': {'route': '/admin/security/roles/{role}/users/{user}', 'category': 'Management'},
    'admin_security_users': {'route': '/admin/security/users', 'category': 'Management'},
    'maintenance_keywords': {'route': '/admin/maintenance/keywords', 'category': 'Management'},
    'maintenance_dates': {'route': '/admin/maintenance/dates', 'category': 'Management'},
    'maintenance_subscriptions': {'route': '/admin/maintenance/subscriptions', 'category': 'Management'},
    'maintenance_conversations': {'route': '/admin/maintenance/conversations', 'category': 'Management'},
    'maintenance_exception': {'route': '/admin/maintenance/exceptions/{hash}', 'category': 'Management'},
}

RESOURCES = {}
RESOURCES.update(PUBLIC_RESOURCES)
RESOURCES.update(RESTRICTED_RESOURCES)
RESOURCES.update(INFO_RESOURCES)
