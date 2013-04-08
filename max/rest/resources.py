PUBLIC_RESOURCES = {
    'users': {'route': '/people'},  # (GET) documented tested
    'user': {'route': '/people/{username}'},  # (GET, PUT, POST) documented tested
    'avatar': {'route': '/people/{username}/avatar'},  # (GET) documented
    'user_activities': {'route': '/people/{username}/activities'},  # (GET, POST) documented tested; ADMIN (GET, POST) documented tested

    'activities': {'route': '/activities'},  # (GET) documented tested
    'activity': {'route': '/activities/{activity}'},  # not public API
    'timeline': {'route': '/people/{username}/timeline'},  # (GET) documented tested

    'comments': {'route': '/activities/{activity}/comments'},  # (GET, POST) documented tested

    'subscriptions': {'route': '/people/{username}/subscriptions'},  # (GET, POST) documented tested
    'subscription': {'route': '/people/{username}/subscriptions/{hash}'},  # (DELETE) documented tested

    'user_conversations': {'route': '/people/{username}/conversations'},  # (GET, POST) documented tested
    'user_conversation': {'route': '/people/{username}/conversations/{id}'},  # (DELETE) documented tested

    'contexts': {'route': '/contexts'},  # (POST GET) documented tested
    'context': {'route': '/contexts/{hash}'},  # (GET, PUT, DELETE) documented tested
    'context_avatar': {'route': '/contexts/{hash}/avatar'},  # (GET) documented
    'public_contexts': {'route': '/contexts/public'},  # (GET)
    'context_user_permission': {'route': '/contexts/{hash}/permissions/{username}/{permission}'},  # (PUT, DELETE) documented tested
    'context_activities': {'route': '/contexts/{hash}/activities'},  # (POST) documented tested


    # MAX 3.0
    'conversations': {'route': '/conversations'},  # (GET, POST) documented tested
    'conversation': {'route': '/conversations/{id}'},  # (GET, DELETE, PUT)
    'messages': {'route': '/conversations/{id}/messages'},  # (GET, POST) documented tested
    'message': {'route': '/conversations/{id}/messages/{activity}'},  # (GET, POST) documented tested
    'participants': {'route': '/conversations/{id}/participants'},
    'participant': {'route': '/conversations/{id}/participant'},

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

}

RESTRICTED_RESOURCES = {

    'admin_security': {'route': '/admin/security'},
}

RESOURCES = {}
RESOURCES.update(PUBLIC_RESOURCES)
RESOURCES.update(RESTRICTED_RESOURCES)
