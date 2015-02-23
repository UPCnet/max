# -*- coding: utf-8 -*-
from max.exceptions import ConnectionError
from max.resources import getMAXSettings

from maxcarrot import RabbitClient
from maxcarrot import RabbitMessage
from socket import error as socket_error

import datetime
import json
import pkg_resources
import sys


def noop(*args, **kwargs):
    """
        Dummy method executed in replacement of the requested method
        when rabbitmq is not defined (i.e. in tests)
    """
    pass


class RabbitNotifications(object):
    """
        Wrapper to access notification methods, and catch possible exceptions
    """

    def __init__(self, request):
        self.request = request
        settings = getMAXSettings(request)
        self.url = settings.get('max_rabbitmq', '')
        self.message_defaults = settings.get('max_message_defaults', {})
        self.enabled = True

        client_properties = {
            "product": "max",
            "version": pkg_resources.require('max')[0].version,
            "platform": 'Python {0.major}.{0.minor}.{0.micro}'.format(sys.version_info),
            "server": settings.get('max_server', '')
        }

        try:
            self.client = RabbitClient(self.url, client_properties=client_properties)
        except AttributeError:
            self.enabled = False
        except socket_error:
            raise ConnectionError("Could not connect to rabbitmq broker")

    def __getattribute__(self, name):
        """
            Returns the requested method if notifier is enabled, otherwise
            performs a noop
        """
        enabled = object.__getattribute__(self, 'enabled')
        if enabled or name in ['enabled', 'url', 'request', 'client', 'message_defaults']:
            return object.__getattribute__(self, name)
        else:
            return noop

    def restart_tweety(self):
        """
            Sends a timestamp to tweety_restart queue, trough the default exchange
            (binding to tweety_restart queue is implicit in this special exchange)
        """
        default_exchange = ''
        restart_request_time = datetime.datetime.now().strftime('%s.%f')
        self.client.send(default_exchange, restart_request_time, 'tweety_restart')
        #self.client.disconnect()

    def add_user(self, username):
        """
            Creates the specified user exchange and bindings
        """
        self.client.create_user(username)
        #self.client.disconnect()

    def delete_user(self, username):
        """
            Deletes the specified user exchange and bindings
        """
        self.client.delete_user(username)
        #self.client.disconnect()

    def bind_user_to_context(self, context, username):
        """
            Creates a binding between user exchanges and a context
        """
        context_id = context.getIdentifier()
        self.client.activity.bind_user(context_id, username)
        #self.client.disconnect()

    def unbind_user_from_context(self, context, username):
        """
            Destroys a binding between user exchanges and a context
        """
        context_id = context.getIdentifier()
        self.client.activity.unbind_user(context_id, username)
        #self.client.disconnect()

    def unbind_context(self, context):
        """
            Destroys all bindings between a context and any user
        """
        context_id = context.getIdentifier()
        self.client.activity.delete(context_id)
        #self.client.disconnect()

    def bind_user_to_conversation(self, conversation, username):
        """
            Creates a binding between user exchanges and a conversation
        """
        context_id = conversation.getIdentifier()
        self.client.conversations.bind_user(context_id, username)
        #self.client.disconnect()

    def unbind_user_from_conversation(self, conversation, username):
        """
            Destroys a binding between user exchanges and a conversation
        """
        context_id = conversation.getIdentifier()
        self.client.conversations.unbind_user(context_id, username)
        #self.client.disconnect()

    def unbind_conversation(self, conversation):
        """
            Destroys all bindings between a conversation and any user
        """
        context_id = conversation.getIdentifier()
        self.client.conversations.delete(context_id)
        #self.client.disconnect()

    def notify_context_activity(self, activity):
        """
            Sends a Carrot (TM) notification of a new post on a context
        """
        message = RabbitMessage()
        message.prepare(self.message_defaults)
        message.update({
            "user": {
                'username': self.request.actor.username,
                'displayname': self.request.actor.displayName,
            },
            "action": "add",
            "object": "activity",
            "data": {
                'text': activity['object'].get('content', '')
            }
        })
        self.client.send('activity', json.dumps(message.packed), activity['contexts'][0]['hash'])
        #self.client.disconnect()

    def notify_context_activity_comment(self, activity, comment):
        """
            Sends a Carrot (TM) notification of a new post on a context
        """
        message = RabbitMessage()
        message.prepare(self.message_defaults)
        message.update({
            "user": {
                'username': self.request.actor.username,
                'displayname': self.request.actor.displayName,
            },
            "action": "add",
            "object": "activity",
            "data": {
                'text': comment['content']
            }
        })
        self.client.send('activity', json.dumps(message.packed), activity['contexts'][0]['hash'])
        #self.client.disconnect()

    def add_conversation(self, conversation):
        """
            Sends a Carrot (TM) notification of a new conversation creation
        """
        conversation_id = conversation.getIdentifier()
        participants_usernames = [user['username'] for user in conversation['participants']]
        self.client.conversations.create(conversation_id, users=participants_usernames)

        # Send a conversation creation notification to rabbit
        message = RabbitMessage()
        message.prepare(self.message_defaults)
        message.update({
            "user": {
                'username': self.request.actor.username,
                'displayname': self.request.actor.displayName,
            },
            "action": "add",
            "object": "conversation",
            "data": {}
        })
        self.client.send('conversations', json.dumps(message.packed), routing_key='{}.notifications'.format(conversation_id))
        #self.client.disconnect()
