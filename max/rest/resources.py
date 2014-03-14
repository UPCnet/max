PUBLIC_RESOURCES = {
    'endpoints': {'route': '/endpoints'},

    'users': {'route': '/people', 'category': 'User', 'name': 'Users'},
    'user': {'route': '/people/{username}', 'category': 'User', 'name': 'User'},
    'avatar': {'route': '/people/{username}/avatar', 'category': 'User', 'name': 'User avatar'},
    'avatar_sizes': {'route': '/people/{username}/avatar/{size}', 'category': 'User', 'name': 'User avatar sizes'},
    'user_activities': {'route': '/people/{username}/activities', 'category': 'Activities', 'name': 'User activities'},
    'user_device': {'route': '/people/{username}/device/{platform}/{token}', 'category': 'User', 'name': 'User device tokens'},

    'activities': {'route': '/activities', 'category': 'Activities'},
    'comments': {'route': '/activities/comments', 'category': 'Comments'},
    'activity': {'route': '/activities/{activity}', 'category': 'Activities'},
    'timeline': {'route': '/people/{username}/timeline', 'category': 'Activities'},
    'timeline_authors': {'route': '/people/{username}/timeline/authors', 'category': 'Activities'},

    'activity_comments': {'route': '/activities/{activity}/comments', 'category': 'Comments'},
    'activity_comment': {'route': '/activities/{activity}/comments/{comment}', 'category': 'Comments'},

    'subscriptions': {'route': '/people/{username}/subscriptions', 'category': 'Subscriptions'},
    'subscription': {'route': '/people/{username}/subscriptions/{hash}', 'category': 'Subscriptions'},

    'user_conversations': {'route': '/people/{username}/conversations', 'category': 'Conversations'},
    'user_conversation': {'route': '/people/{username}/conversations/{id}', 'category': 'Conversations'},

    'contexts': {'route': '/contexts', 'category': 'Contexts'},
    'context': {'route': '/contexts/{hash}', 'category': 'Contexts'},
    'context_avatar': {'route': '/contexts/{hash}/avatar', 'category': 'Contexts'},
    'public_contexts': {'route': '/contexts/public', 'category': 'Contexts'},
    'context_user_permissions_defaults': {'route': '/contexts/{hash}/permissions/{username}/defaults', 'category': 'Contexts'},
    'context_user_permission': {'route': '/contexts/{hash}/permissions/{username}/{permission}', 'category': 'Contexts'},
    'context_activities': {'route': '/contexts/{hash}/activities', 'category': 'Activities'},
    'context_comments': {'route': '/contexts/{hash}/comments', 'category': 'Comments'},
    'context_activities_authors': {'route': '/contexts/{hash}/activities/authors', 'category': 'Activities'},
    'context_subscriptions': {'route': '/contexts/{hash}/subscriptions', 'category': 'Contexts'},
    'context_tags': {'route': '/contexts/{hash}/tags', 'category': 'Contexts'},
    'context_tag': {'route': '/contexts/{hash}/tags/{tag}', 'category': 'Contexts'},

    # MAX 3.0
    'conversations': {'route': '/conversations', 'category': 'Conversations'},
    'conversation': {'route': '/conversations/{id}', 'category': 'Conversations'},
    'conversation_owner': {'route': '/conversations/{id}/owner', 'category': 'Conversations'},
    'conversation_avatar': {'route': '/conversations/{id}/avatar', 'category': 'Conversations'},
    'pushtokens': {'route': '/conversations/{id}/tokens', 'category': 'Conversations'},
    'messages': {'route': '/conversations/{id}/messages', 'category': 'Conversations'},
    'message': {'route': '/conversations/{id}/messages/{activity}', 'category': 'Conversations'},
    'participants': {'route': '/conversations/{id}/participants', 'category': 'Conversations'},
    'participant': {'route': '/conversations/{id}/participant', 'category': 'Conversations'},

    # MAX 3.6
    'likes': {'route': '/activities/{activity}/likes', 'category': 'Activities'},
    'like': {'route': '/activities/{activity}/likes/{username}', 'category': 'Activities'},
    'user_likes': {'route': '/people/{username}/likes', 'category': 'User', 'name': 'User liked activity'},
    'favorites': {'route': '/activities/{activity}/favorites', 'category': 'Activities'},
    'favorite': {'route': '/activities/{activity}/favorites/{username}', 'category': 'Activities'},
    'user_favorites': {'route': '/people/{username}/favorites', 'category': 'User', 'name': 'User favorited activities'},


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
