from pyramid.view import view_config

from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot
from max.decorators import MaxRequest, MaxResponse


@view_config(route_name='timeline', request_method='GET')
@MaxResponse
@MaxRequest
def getUserTimeline(context, request):
    """
         /users/{displayName}/timeline

         Retorna totes les activitats d'un usuari
    """
    displayName = request.matchdict['displayName']
    is_context_resource = 'timeline/contexts' in request.path
    is_follows_resource = 'timeline/follows' in request.path

    mmdb = MADMaxDB(context.db)

    actor = mmdb.users.getItemsBydisplayName(displayName)[0]

    actor_query = {'actor._id': actor['_id']}

    # Add the activity of the people that the user follows
    actors_followings = []
    for following in actor['following']['items']:
        followed_person = mmdb.users.getItemsBydisplayName(following['displayName'])[0]
        if followed_person:
            actors_followings.append({'actor._id': followed_person['_id']})

    # Add the activity of the people that posts to a particular context
    contexts_followings = []
    for subscribed in actor['subscribedTo']['items']:
        contexts_followings.append({'contexts.url': subscribed['url']})

    query_items = []

    if not is_follows_resource and not is_context_resource:
        query_items.append(actor_query)
        query_items += actors_followings
        query_items += contexts_followings

    if is_context_resource:
        query_items += contexts_followings

    if is_follows_resource:
        query_items += contexts_followings

    if query_items:
        query = {'$or': query_items}
        activities = mmdb.activity.search(query, sort="_id", limit=10, flatten=1)
    else:
        activities = []

    handler = JSONResourceRoot(activities)
    return handler.buildResponse()
