PUBLIC_RESOURCES = {
    'users': {'route': '/people'},
    'user': {'route': '/people/{username}'},
    'avatar': {'route': '/people/{username}/avatar'},
    'user_activities': {'route': '/people/{username}/activities'},
    'user_device': {'route': '/people/{username}/device/{platform}/{token}'},

    'activities': {'route': '/activities'},
    'comments': {'route': '/activities/comments'},
    'activity': {'route': '/activities/{activity}'},
    'timeline': {'route': '/people/{username}/timeline'},
    'timeline_authors': {'route': '/people/{username}/timeline/authors'},

    'activity_comments': {'route': '/activities/{activity}/comments'},
    'activity_comment': {'route': '/activities/{activity}/comments/{comment}'},

    'subscriptions': {'route': '/people/{username}/subscriptions'},
    'subscription': {'route': '/people/{username}/subscriptions/{hash}'},

    'user_conversations': {'route': '/people/{username}/conversations'},
    'user_conversation': {'route': '/people/{username}/conversations/{id}'},

    'contexts': {'route': '/contexts'},
    'context': {'route': '/contexts/{hash}'},
    'context_avatar': {'route': '/contexts/{hash}/avatar'},
    'public_contexts': {'route': '/contexts/public'},
    'context_user_permissions_defaults': {'route': '/contexts/{hash}/permissions/{username}/defaults'},
    'context_user_permission': {'route': '/contexts/{hash}/permissions/{username}/{permission}'},
    'context_activities': {'route': '/contexts/{hash}/activities'},
    'context_activities_authors': {'route': '/contexts/{hash}/activities/authors'},
    'context_subscriptions': {'route': '/contexts/{hash}/subscriptions'},
    'context_tags': {'route': '/contexts/{hash}/tags'},
    'context_tag': {'route': '/contexts/{hash}/tags/{tag}'},

    # MAX 3.0
    'conversations': {'route': '/conversations'},
    'conversation': {'route': '/conversations/{id}'},
    'conversation_avatar': {'route': '/conversations/{id}/avatar'},
    'pushtokens': {'route': '/conversations/{id}/tokens'},
    'messages': {'route': '/conversations/{id}/messages'},
    'message': {'route': '/conversations/{id}/messages/{activity}'},
    'participants': {'route': '/conversations/{id}/participants'},
    'participant': {'route': '/conversations/{id}/participant'},

    # MAX 3.6
    'likes': {'route': '/activities/{activity}/likes'},
    'like': {'route': '/activities/{activity}/likes/{username}'},
    'user_likes': {'route': '/people/{username}/likes'},
    'favorites': {'route': '/activities/{activity}/favorites'},
    'favorite': {'route': '/activities/{activity}/favorites/{username}'},
    'user_favorites': {'route': '/people/{username}/favorites'},


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

    'admin_security': {'route': '/admin/security'},
    'admin_security_role': {'route': '/admin/security/roles/{role}'},
    'admin_security_role_user': {'route': '/admin/security/roles/{role}/users/{user}'},
    'maintenance_keywords': {'route': '/admin/maintenance/keywords'},
    'maintenance_dates': {'route': '/admin/maintenance/dates'},
    'maintenance_subscriptions': {'route': '/admin/maintenance/subscriptions'},
    'maintenance_conversations': {'route': '/admin/maintenance/conversations'}
}

AUTHENTICATION_RESOURCES = {
    'auth_user': {'route': '/auth/user'},
    'auth_vhost': {'route': '/auth/vhost'},
    'auth_resource': {'route': '/auth/resource'},
}

RESOURCES = {}
RESOURCES.update(PUBLIC_RESOURCES)
RESOURCES.update(RESTRICTED_RESOURCES)
RESOURCES.update(AUTHENTICATION_RESOURCES)
