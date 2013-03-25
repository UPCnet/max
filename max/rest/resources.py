PUBLIC_RESOURCES = {
    'users': {'route': '/people'},  # (GET) documented tested
    'user': {'route': '/people/{username}'},  # (GET, PUT, POST) documented tested
    'avatar': {'route': '/people/{username}/avatar'},  # (GET) documented
    'user_activities': {'route': '/people/{username}/activities'},  # (GET, POST) documented tested

    'activities': {'route': '/activities'},  # (GET) documented tested
    'timeline': {'route': '/people/{username}/timeline'},  # (GET) documented tested

    'comments': {'route': '/activities/{activity}/comments'},  # (GET, POST) documented tested

    'context_avatar': {'route': '/contexts/{hash}/avatar'},  # (GET) documented

    'subscriptions': {'route': '/people/{username}/subscriptions'},  # (GET, POST) documented tested
    'subscription': {'route': '/people/{username}/subscriptions/{hash}'},  # (DELETE) documented tested

    # MAX 3.0
    'conversations': {'route': '/conversations'},  # (GET, POST) documented tested
    'messages': {'route': '/conversations/{hash}/messages'},  # (GET, POST) documented tested

    # MAX 4.0
    'user_shares': {'route': '/people/{username}/shares'},  # not implemented
    'user_likes': {'route': '/people/{username}/likes'},  # not implemented
    'follows': {'route': '/people/{username}/follows'},  # not implemented
    'follow': {'route': '/people/{username}/follows/{followedDN}'},  # not implemented
    'likes': {'route': '/activities/{activity}/likes'},  # not implemented
    'like': {'route': '/activities/{activity}/likes/{likeId}'},  # not implemented
    'shares': {'route': '/activities/{activity}/shares'},  # not implemented
    'share': {'route': '/activities/{activity}/shares/{shareId}'},  # not implemented

    # Not implemented / Not in roadmap
    'user_comments': {'route': '/people/{username}/comments'},  # not implemented
    'user_conversations': {'route': '/people/{username}/conversations'},  # not implemented
    'comment': {'route': '/activities/{activity}/comments/{commentId}'},  # not implemented
    'context_permissions': {'route': '/contexts/{hash}/permissions'},  # not implemented
    'context_user_permissions': {'route': '/contexts/{hash}/permissions/{username}'},  # not implemented
    'conversation': {'route': '/conversations/{hash}'},  # not implemented

}

RESTRICTED_RESOURCES = {

    'context': {'route': '/contexts/{hash}'},  # (GET, PUT, DELETE) documented tested
    'contexts': {'route': '/contexts'},  # (POST) documented tested
    'activity': {'route': '/activities/{activity}'},  # not public API

    'context_user_permission': {'route': '/contexts/{hash}/permissions/{username}/{permission}'},  # (PUT, DELETE) documented tested

    'admin_user_activities': {'route': '/admin/people/{username}/activities'},  # (POST) documented tested
    'admin_context_activities': {'route': '/admin/contexts/{hash}/activities'},  # (POST) documented tested
    'admin_subscriptions': {'route': '/admin/people/{username}/subscriptions'},  # (POST) documented tested
    'admin_subscription': {'route': '/admin/people/{username}/subscriptions/{hash}'},  # (DELETE) documented tested
    'admin_users': {'route': '/admin/people'},
    'admin_activities': {'route': '/admin/activities'},
    'admin_contexts': {'route': '/admin/contexts'},

    'admin_user': {'route': '/admin/people/{id}'},
    'admin_activity': {'route': '/admin/activities/{id}'},
    'admin_context': {'route': '/admin/contexts/{id}'},

    'admin_security': {'route': '/admin/security'},
}

RESOURCES = {}
RESOURCES.update(PUBLIC_RESOURCES)
RESOURCES.update(RESTRICTED_RESOURCES)
