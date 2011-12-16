from pyramid.view import view_config

from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot


@view_config(route_name='timeline', request_method='GET')
def UserTimeline(context, request):
    """
         /users/{displayName}/timeline

         Retorna totes les activitats d'un usuari
    """
    displayName = request.matchdict['user_displayName']

    mmdb = MADMaxDB(context.db)

    actor = mmdb.users.getItemsBydisplayName(displayName)[0]

    actor_query = {'actor._id': actor['_id']}
    
    # Add the activity of the people that the user follows
    actors_followings = []
    for following in actor['following']['items']:
        actors_followings.append({'actor._id': following['_id']})

    # Add the activity of the people that posts to a particular context
    contexts_followings = []
    for subscribed in actor['subscribedTo']['items']:
        contexts_followings.append({'target.url': subscribed['url']})

    
    query = {'$or' : [ actor_query ] + actors_followings + contexts_followings}

    activities = mmdb.activity.search(query,sort="_id",limit=10,flatten=1)

    handler = JSONResourceRoot(activities)
    return handler.buildResponse()

