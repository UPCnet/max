# -*- coding: utf-8 -*-
from max.exceptions import ObjectNotFound
from max.models import Context
from max.models import Token
from max.models import Conversation
from max.rest import JSONResourceEntity
from max.rest import JSONResourceRoot
from max.rest import endpoint
from max.security.permissions import do_maintenance
from max.rabbitmq import RabbitNotifications
from max import maxlogger

from pyramid.httpexceptions import HTTPNoContent

from bson import ObjectId
from datetime import datetime

import glob
import os
import re
from collections import defaultdict

@endpoint(route_name='maintenance_keywords', request_method='POST', permission=do_maintenance)
def rebuildKeywords(context, request):
    """
        Rebuild keywords of all activities
    """
    activities = request.db.activity.search({'verb': 'post'})
    for activity in activities:
        activity['object'].setKeywords()
        activity.setKeywords()
        activity.save()

    handler = JSONResourceRoot(request, [])
    return handler.buildResponse()


@endpoint(route_name='maintenance_dates', request_method='POST', permission=do_maintenance)
def rebuildDates(context, request):
    """
        Rebuild dates of activities

        Now currently sets the lastComment id field
    """
    activities = request.db.activity.search({'verb': 'post'})
    for activity in activities:
        # Remove ancient commented field
        if 'commented' in activity:
            del activity['commented']
        if activity.get('replies', []):
            activity['lastComment'] = ObjectId(activity['replies'][-1]['id'])
        activity.save()

    handler = JSONResourceRoot(request, [])
    return handler.buildResponse()


@endpoint(route_name='maintenance_subscriptions', request_method='POST', permission=do_maintenance)
def rebuildSubscriptions(context, request):
    """
        Rebuild context subscriptions

        Performs sanity checks on existing subscriptions
    """
    existing_contexts = {}
    contexts = request.db.contexts.dump()
    for context in contexts:
        context.updateUsersSubscriptions(force_update=True)
        context.updateContextActivities(force_update=True)
        existing_contexts[context['hash']] = context

        #Creates a binding between user exchanges and a context
        notifier = RabbitNotifications(request)
        if context.get('notifications', False):
            for user in context.subscribedUsers():
                notifier.bind_user_to_context(context, user['username'])

    users = request.db.users.search({'subscribedTo.0': {'$exists': True}})
    for user in users:
        for subscription in user.get('subscribedTo', []):
            if subscription['hash'] not in existing_contexts:
                fake_deleted_context = Context.from_object(request, subscription)
                user.removeSubscription(fake_deleted_context)
            else:
                subscription.pop('vetos', None)
                subscription.pop('grants', None)
        user.save()
    handler = JSONResourceRoot(request, [])
    maxlogger.warning("Finalizado rebuildSubscriptions (crea los bindings de los usuarios subscritos en un contexto, si no los tiene): " + str(handler.buildResponse()._status) + " realizado el: " + datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
    return handler.buildResponse()


@endpoint(route_name='maintenance_conversations', request_method='POST', permission=do_maintenance)
def rebuildConversationSubscriptions(context, request):
    """
        Rebuild conversation subscriptions

        Performs sanity checks on existing subscriptions
    """
    existing_conversations = {}
    conversations = request.db.conversations.dump()
    for conversation in conversations:

        # if we found an ancient plain username list, we migrate it
        if True not in [isinstance(a, dict) for a in conversation['participants']]:
            conversation['participants'] = [{'username': a, 'displayName': a, 'objectType': 'person'} for a in conversation['participants']]

        conversation.save()

        conversation.updateUsersSubscriptions(force_update=True)
        conversation.updateContextActivities(force_update=True)

        existing_conversations[str(conversation['_id'])] = conversation

    subscribed_users_by_conversation = {}
    users = request.db.users.search({'talkingIn.0': {'$exists': True}})
    for user in users:
        for subscription in user.get('talkingIn', []):
            if subscription['id'] not in existing_conversations:
                fake_deleted_conversation = Conversation.from_object(request, subscription)
                user.removeSubscription(fake_deleted_conversation)
                user['talkingIn'] = [a for a in user['talkingIn'] if a['id'] != subscription['id']]
            else:
                # if subscription has an ancient plain username list, update and save it
                if True not in [isinstance(a, dict) for a in subscription['participants']]:
                    subscription['participants'] = existing_conversations[subscription['id']]['participants']
            subscribed_users_by_conversation.setdefault(subscription['id'], [])
            subscribed_users_by_conversation[subscription['id']].append(user['username'])

        user.updateConversationParticipants(force_update=True)
        user.save()

    existing_users = request.db.users.search({}, show_fields={'username': True, '_id': False})
    existing_users_set = set([a['username'] for a in existing_users])

    conversations = request.db.conversations.dump()
    try:
        for conversation in conversations:
            conversation_participants_usernames = [user['username'] for user in conversation['participants']]
            conversation_subscribed_usernames = subscribed_users_by_conversation[str(conversation['_id'])]

            not_subscribed = set(conversation_participants_usernames) - set(conversation_subscribed_usernames)
            deleted_participants = set(not_subscribed) - existing_users_set

            all_participants_subscribed = len(conversation_participants_usernames) == len(conversation_subscribed_usernames)
            all_participants_exist = len(deleted_participants) == 0
            if 'single' in conversation['tags']:
                conversation['tags'].remove('single')
            if 'archive' in conversation['tags']:
                conversation['tags'].remove('archive')

            # Conversations od 2+ get the group tag
            if len(conversation['participants']) > 2:
                if 'group' not in conversation['tags']:
                    conversation['tags'].append('group')
            # Two people conversation and not group:
            # tag single: if not all participants subscribed by all exist
            # tag archive: if not all participants exist
            elif len(conversation['participants']) == 2 and 'group' not in conversation['tags']:
                if all_participants_subscribed:
                    pass
                elif not all_participants_subscribed and all_participants_exist:
                    conversation['tags'].append('single')
                elif not all_participants_subscribed and not all_participants_exist:
                    conversation['tags'].append('archive')
            # Tag archive: if group conversation only 1 participant
            elif 'group' in conversation['tags'] and len(conversation['participants']) == 1:
                conversation['tags'].append('archive')

            # Creates a binding only users subscribed in conversation
            notifier = RabbitNotifications(request)
            for participant in conversation_subscribed_usernames:
                notifier.bind_user_to_conversation(conversation, participant)

            conversation.save()
    except:
        # Si hi ha alguna conversa on el owner no estigui subscrit a la conversa
        # el que fem es afegir com a owner un dels membres que estigui subscrit
        # i creem els bindings dels usuaris subscrits.
        # He fet això perque en local tenia un grup on el propietari no estaba subscrit i petava
        if conversation['_owner'] not in conversation_subscribed_usernames:
            conversation['_owner'] = conversation_subscribed_usernames[0]
            conversation.save()


            # Give hability to add new users to the new owner
            user = request.db.users.search({'username': str(conversation_subscribed_usernames[0])})
            user.request.actor.grantPermission(subscription, 'invite', permanent=True)
            user.request.actor.grantPermission(subscription, 'kick', permanent=True)
            user.request.actor.revokePermission(subscription, 'unsubscribe', permanent=True)

            # Creates a binding only users subscribed in conversation
            notifier = RabbitNotifications(request)
            for participant in conversation_subscribed_usernames:
                notifier.bind_user_to_conversation(conversation, participant)

            conversation.save()

    handler = JSONResourceRoot(request, [])
    maxlogger.warning("Finalizado rebuildConversationSubscriptions (crea los bindings de los usuarios subscritos en una conversa, si no los tiene): " + str(handler.buildResponse()._status) + " realizado el: " + datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
    return handler.buildResponse()


@endpoint(route_name='maintenance_users', request_method='POST', permission=do_maintenance)
def rebuildUser(context, request):
    """
        Rebuild users

        Sets sensible defaults and perform consistency checks.
        Checks that owner of the object must be the same as the user object
    """
    users = request.db.users.dump()
    for user in users:
        if user['_owner'] != user['username']:
            user['_owner'] = user['username']
            user.save()

        # Create exchange publish and subscribe in Rabbit
        # Hemos visto que si el usuario ya esta creado no pasa nada y si no existe crea los exchanges
        notifier = RabbitNotifications(request)
        notifier.add_user(user['username'])

    handler = JSONResourceRoot(request, [])
    maxlogger.warning("Finalizado rebuildUser (crea exchanges de los usuarios que no existan en el Rabbit): " + str(handler.buildResponse()._status) + " realizado el: " + datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
    return handler.buildResponse()


@endpoint(route_name='maintenance_tokens', request_method='POST', permission=do_maintenance)
def rebuildTokens(context, request):
    """
        Rebuild tokens

        Move any user that has old style tokens to the new tokens collection
    """
    # Find all users with tokens
    users_with_tokens = request.db.db.users.find({'$or': [{'iosDevices.0': {'$exists': True}}, {'androidDevices.0': {'$exists': True}}]})

    platforms = [
        ('ios', 'iosDevices'),
        ('android', 'androidDevices')
    ]

    for user in users_with_tokens:
        for platform, oldfield in platforms:
            tokens = user.get(oldfield, [])

            for token in tokens:
                newtoken = Token.from_object(request, {
                    'platform': platform,
                    'token': token,
                    'objectId': 'token',
                    '_owner': user['username'],
                    '_creator': user['username'],
                })
                newtoken.setDates()
                newtoken.insert()

    # Clean old token fields
    request.db.db.users.update({}, {'$unset': {'iosDevices': '', 'androidDevices': ''}}, multi=True)

    handler = JSONResourceRoot(request, [])
    return handler.buildResponse()


@endpoint(route_name='maintenance_exception', request_method='GET', permission=do_maintenance)
def getException(context, request):
    """
        Get an exception
    """
    ehash = request.matchdict['hash']
    exceptions_folder = request.registry.settings.get('exceptions_folder')
    matches = glob.glob('{}/*{}'.format(exceptions_folder, ehash))

    if not matches:
        raise ObjectNotFound("There is no logged exception with this hash")

    exception = open(matches[0]).read()
    regex = r'BEGIN EXCEPTION REPORT: .*?\nDATE: (.*?)\nREQUEST:\n\n(.*?)\n\nTRACEBACK:\n\n(.*?)\nEND EXCEPTION REPORT'
    match = re.search(regex, exception, re.DOTALL)

    date, http_request, traceback = match.groups()

    result = {
        'date': date,
        'request': http_request,
        'traceback': traceback
    }
    handler = JSONResourceEntity(request, result)
    return handler.buildResponse()


@endpoint(route_name='maintenance_exception', request_method='DELETE', permission=do_maintenance)
def deleteException(context, request):
    """
        Delete an exception
    """
    ehash = request.matchdict['hash']
    exceptions_folder = request.registry.settings.get('exceptions_folder')
    matches = glob.glob('{}/*{}'.format(exceptions_folder, ehash))

    if not matches:
        raise ObjectNotFound("There is no logged exception with this hash")

    os.remove(matches[0])
    return HTTPNoContent()


@endpoint(route_name='maintenance_exceptions', request_method='GET', permission=do_maintenance)
def getExceptions(context, request):
    """
        Get all exceptions
    """
    exceptions_folder = request.registry.settings.get('exceptions_folder')
    exception_files = os.listdir(exceptions_folder)

    def get_exceptions():
        for exception_filename in exception_files:
            try:
                logger, date, exception_id = exception_filename.split('_')
            except:
                pass

            yield {
                'id': exception_id,
                'date': datetime.strptime(date, '%Y%m%d%H%M%S').strftime('%Y/%m/%d %H:%M:%S')
            }

    handler = JSONResourceRoot(request, sorted(get_exceptions(), key=lambda x: x['date'], reverse=True))
    return handler.buildResponse()
