# -*- coding: utf-8 -*-
from max import SEARCH_MODIFIERS
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


@endpoint(
    route_name='users', request_method='GET',
    permission=list_visible_people,
    modifiers=SEARCH_MODIFIERS + ['twitter_enabled'])
def getVisibleUsers(users, request):
    """
        Search users

        Return a list of persons of the system, optionaly filtered using the available
        modifiers.

        The objects returned by this endpoint are intended for user listing and
        searching, so only username and displayName attributes of a person are returned. If you
        need the full profile of a user, use the `GET` endpoint of the `User` resource.
    """
    query = {}

    filter_fields = ["username", "displayName", "objectType", 'subscribedTo']
    found_users = users.search(query, show_fields=filter_fields, sort_by_field="username", flatten=0, **searchParams(request))

    # Filter user results. User

    filtered_users = [user for user in found_users if request.actor.is_allowed_to_see(user)]

    handler = JSONResourceRoot(flatten(filtered_users, squash=['subscribedTo']), remaining=found_users.remaining)
    return handler.buildResponse()


@endpoint(
    route_name='users', request_method='POST',
    permission=add_people,
    modifiers=['notifications'])
def addUser(users, request):
    """
        Add a user

        Creates a new user in the system, with all the attributes provided
        in the posted user object.

        - `username` - Used to identify and login the user. This is the only required parameter and cannot be modified.
        - `displayname` - The full name of the user.
        - `twitterUsername` - A valid Twitter® username (without @ prefix), used on the twitter integration service.


        This operation is idempotent, which means that a request to create a user that already exists,
        will not recreate or overwrite that user. Instead, the existing user object will be returned. You can
        tell when this happens by looking at the HTTP response status code. A new user insertion will return
        a **201 CREATED** code, and with an existing users a **200 OK**.

        + Request

            {
                "username": "user1",
                "displayName": "user2",
                "twitterUsername: "twitteruser",
            }

    """
    payload = request.decoded_payload
    if not isinstance(payload, dict):
        raise ValidationError('Unexpected data type in request')

    username = payload.get('username', None)
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
    handler = JSONResourceEntity(request, newuser.getInfo(), status_code=code)
    return handler.buildResponse()


@endpoint(
    route_name='user', request_method='GET',
    permission=view_user_profile)
def getUser(user, request):
    """
        Get a user
    """
    actor_info = user.getInfo()

    handler = JSONResourceEntity(request, actor_info)
    return handler.buildResponse()


@endpoint(
    route_name='user', request_method='PUT',
    permission=modify_user)
def ModifyUser(user, request):
    """
        Modify a user

        Updates user information stored on the user object. Properties on request
        not previously set will be added and the existing ones overiddeb by the new
        values.

        > Note that properties other than the ones defined on the user creation method,
        > that may be visible on the user profile (like `subscribedTo` or `talkingIn`) are
        > not updatable using this endpoint. You must use the available methods  for that goal.
    """
    properties = user.getMutablePropertiesFromRequest(request)
    user.modifyUser(properties)
    user.updateConversationParticipants()
    handler = JSONResourceEntity(request, user.flatten())
    return handler.buildResponse()


@endpoint(
    route_name='user', request_method='DELETE',
    permission=delete_user)
def deleteUser(user, request):
    """
        Delete a user

        Permanently deletes a user from the system. This operation destroys the user and all its data,
        including subscriptions to contexts and conversations.
    """
    user.delete()
    return HTTPNoContent()
