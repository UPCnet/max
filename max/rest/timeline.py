from pyramid.view import view_config

from max.MADMax import MADMaxDB
from max.rest.ResourceHandlers import JSONResourceRoot
from max.decorators import MaxRequest, MaxResponse
from max.oauth2 import oauth2
from max.rest.utils import searchParams


@view_config(route_name='timeline', request_method='GET')
#@MaxResponse
@MaxRequest
@oauth2(['widgetcli'])
def getUserTimeline(context, request):
    """
         /users/{username}/timeline

         Retorna totes les activitats d'un usuari
    """
    actor = request.actor
    is_context_resource = 'timeline/contexts' in request.path
    is_follows_resource = 'timeline/follows' in request.path

    mmdb = MADMaxDB(context.db)

    actor_query = {'actor._id': actor['_id']}

    # Add the activity of the people that the user follows
    actors_followings = []
    for following in actor['following']['items']:
        followed_person = mmdb.users.getItemsByusername(following['username'])[0]
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
        query['verb'] = 'post'
        activities = mmdb.activity.search(query, sort="_id", flatten=1, **searchParams(request))
    else:
        activities = []

    handler = JSONResourceRoot(activities)
    return handler.buildResponse()
