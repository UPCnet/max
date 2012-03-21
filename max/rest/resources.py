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
'subscription': {'route': '/people/{username}/subscriptions/{urlHash}'},

'activities': {'route': '/activities'},
'activity': {'route': '/activities/{activity}'},
'comments': {'route': '/activities/{activity}/comments'},
'comment': {'route': '/activities/{activity}/comments/{commentId}'},
'likes': {'route': '/activities/{activity}/likes'},
'like': {'route': '/activities/{activity}/likes/{likeId}'},
'shares': {'route': '/activities/{activity}/shares'},
'share': {'route': '/activities/{activity}/shares/{shareId}'},

'contexts': {'route': '/contexts'},
'context': {'route': '/context/{urlHash}'},
'context_permissions': {'route': '/context/{urlHash}/permissions'},
'context_user_permissions': {'route': '/context/{urlHash}/permissions/{username}'},
'context_user_permission': {'route': '/context/{urlHash}/permissions/{username}/{permission}'},
}

ADMIN_RESOURCES = {
'admin_user_activities': {'route': '/admin/people/{username}/activities'},
}

RESOURCES = {}
RESOURCES.update(OAUTH_RESOURCES)
RESOURCES.update(ADMIN_RESOURCES)
