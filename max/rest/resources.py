OAUTH_RESOURCES = {
    'users': {'route': '/people'},
    'user': {'route': '/people/{username}'},
    'avatar': {'route': '/people/{username}/avatar'},
    'user_activities': {'route': '/people/{username}/activities'},
    'timeline': {'route': '/people/{username}/timeline'},
    'user_comments': {'route': '/people/{username}/comments'},
    'user_shares': {'route': '/people/{username}/shares'},
    'user_likes': {'route': '/people/{username}/likes'},
    'follows': {'route': '/people/{username}/follows'},
    'follow': {'route': '/people/{username}/follows/{followedDN}'},
    'subscriptions': {'route': '/people/{username}/subscriptions'},
    'subscription': {'route': '/people/{username}/subscriptions/{hash}'},
    'user_conversations': {'route': '/people/{username}/conversations'},

    'activities': {'route': '/activities'},
    'activity': {'route': '/activities/{activity}'},
    'comments': {'route': '/activities/{activity}/comments'},
    'comment': {'route': '/activities/{activity}/comments/{commentId}'},
    'likes': {'route': '/activities/{activity}/likes'},
    'like': {'route': '/activities/{activity}/likes/{likeId}'},
    'shares': {'route': '/activities/{activity}/shares'},
    'share': {'route': '/activities/{activity}/shares/{shareId}'},

    'contexts': {'route': '/contexts'},
    'context': {'route': '/contexts/{hash}'},
    'context_avatar': {'route': '/contexts/{hash}/avatar'},
    'context_permissions': {'route': '/contexts/{hash}/permissions'},
    'context_user_permissions': {'route': '/contexts/{hash}/permissions/{username}'},
    'context_user_permission': {'route': '/contexts/{hash}/permissions/{username}/{permission}'},

    'conversations': {'route': '/conversations'},  # documented
    'messages': {'route': '/conversations/{hash}/messages'},

}
# POST a conversation es enviar un Missatge
# GET a messages es agafar dades dels missatges de la conversa

ADMIN_RESOURCES = {
    'admin_user_activities': {'route': '/admin/people/{username}/activities'},
    'admin_context_activities': {'route': '/admin/contexts/{hash}/activities'},
    'admin_users': {'route': '/admin/people'},
    'admin_activities': {'route': '/admin/activities'},
    'admin_contexts': {'route': '/admin/contexts'},

    'admin_user': {'route': '/admin/people/{id}'},
    'admin_activity': {'route': '/admin/activities/{id}'},
    'admin_context': {'route': '/admin/contexts/{id}'},
}

RESOURCES = {}
RESOURCES.update(OAUTH_RESOURCES)
RESOURCES.update(ADMIN_RESOURCES)
