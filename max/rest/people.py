# -*- coding: utf-8 -*-
from max.exceptions import ValidationError
from max.models import User
from max.rabbitmq import RabbitNotifications
from max.rest import JSONResourceEntity
from max.rest import JSONResourceRoot
from max.rest import endpoint
from max.utils.dicts import flatten
from max.utils import searchParams
from max.security.permissions import add_people
from max.security.permissions import delete_user
from max.security.permissions import list_visible_people
from max.security.permissions import modify_user
from max.security.permissions import view_user_profile

from pyramid.httpexceptions import HTTPNoContent
from pyramid.settings import asbool


@endpoint(route_name='users', request_method='GET', permission=list_visible_people, requires_actor=True)
def getVisibleUsers(users, request):
    """
         /people

         Return the result of a query specified by the username param as
         a list of usernames. For UI use only.
    """
    query = {}

    filter_fields = ["username", "displayName", "objectType", 'subscribedTo']
    found_users = users.search(query, show_fields=filter_fields, sort_by_field="username", flatten=0, **searchParams(request))
    remaining = found_users.remaining

    # Filter user results. User

    filtered_users = [user for user in found_users if request.actor.is_allowed_to_see(user)]

    handler = JSONResourceRoot(flatten(filtered_users, squash=['subscribedTo']), remaining=remaining)
    return handler.buildResponse()


@endpoint(route_name='users', request_method='POST', permission=add_people, requires_actor=False)
def addUser(users, request):
    """
        /people

        [RESTRICTED] Creates a system user.
    """
    username = request.actor_username
    if username is None:
        raise ValidationError('Missing username in request')

    rest_params = {'username': username.lower()}

    # Initialize a User object from the request
    newuser = User.from_request(request, rest_params=rest_params)

    # If we have the _id setted, then the object already existed in the DB,
    # otherwise, proceed to insert it into the DB
    # In both cases, respond with the JSON of the object and the appropiate
    # HTTP Status Code

    if newuser.get('_id'):
        # Already Exists
        code = 200

        # Determine if we have to recreate exchanges for an existing user
        # Defaults NOT to recreate them if not specified
        create_exchanges = asbool(request.params.get('notifications', False))
        if create_exchanges:
            notifier = RabbitNotifications(request)
            notifier.add_user(username)
    else:
        # New User
        code = 201

        # Determine if we have to recreate exchanges for a new user
        # Defaults to Create them if not specified
        create_exchanges = asbool(request.params.get('notifications', True))
        userid = newuser.insert(notifications=create_exchanges)

        newuser['_id'] = userid
    handler = JSONResourceEntity(newuser.flatten(), status_code=code)
    return handler.buildResponse()


@endpoint(route_name='user', request_method='GET', permission=view_user_profile, requires_actor=True)
def getUser(user, request):
    """
        /people/{username}

        Return the required user object.
    """

    # Flattened actor will contain only the visible fields for the current user
    # So we will only prepare the calculated conversations  (lastMessage & displayName)
    # if we have permission to view the talkingIn field

    actor_info = user.getInfo()

    handler = JSONResourceEntity(actor_info)
    return handler.buildResponse()


@endpoint(route_name='user', request_method='PUT', permission=modify_user, requires_actor=True)
def ModifyUser(user, request):
    """
        /people/{username}

        Modifies a system user via oauth, so only the user can modify its own
        properties.
    """
    properties = user.getMutablePropertiesFromRequest(request)
    user.modifyUser(properties)
    user.updateConversationParticipants()
    handler = JSONResourceEntity(user.flatten())
    return handler.buildResponse()


@endpoint(route_name='user', request_method='DELETE', permission=delete_user, requires_actor=True)
def deleteUser(user, request):
    """
    """
    user.delete()
    return HTTPNoContent()
