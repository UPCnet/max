# -*- coding: utf-8 -*-
from max.resources import getMAXSettings
from pyramid.threadlocal import get_current_request

import pika
import json
import datetime

from maxcarrot import RabbitClient
from maxcarrot import RabbitMessage


def restartTweety():
    settings = getMAXSettings(get_current_request())
    rabbitmq_url = settings.get('max_rabbitmq', None)
    # If pika_parameters is not defined, then we assume that we are on tests
    if rabbitmq_url:
        connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        channel = connection.channel()
        restart_request_time = datetime.datetime.now().strftime('%s.%f')
        channel.basic_publish(
            exchange='',
            routing_key='tweety_restart',
            body=restart_request_time)


def addUser(username):
    settings = getMAXSettings(get_current_request())
    rabbitmq_url = settings.get('max_rabbitmq', None)

    # If rabbitmq_url is not defined, then we assume that we are on tests and do nothing
    if rabbitmq_url:
        server = RabbitClient(rabbitmq_url)
        server.create_user(username)
        server.disconnect()


def bindUserToContext(context, username):
    request = get_current_request()
    settings = getMAXSettings(request)
    rabbitmq_url = settings.get('max_rabbitmq', None)

    # If rabbitmq_url is not defined, then we assume that we are on tests and do nothing
    if rabbitmq_url:
        server = RabbitClient(rabbitmq_url)
        context_id = context.getIdentifier()
        server.activity.bind_user(context_id, username)
        server.disconnect()


def unbindUserFromContext(context, username):
    request = get_current_request()
    settings = getMAXSettings(request)
    rabbitmq_url = settings.get('max_rabbitmq', None)

    # If rabbitmq_url is not defined, then we assume that we are on tests and do nothing
    if rabbitmq_url:
        server = RabbitClient(rabbitmq_url)
        context_id = context.getIdentifier()
        server.activity.unbind_user(context_id, username)
        server.disconnect()


def notifyContextActivity(activity):
    request = get_current_request()
    settings = getMAXSettings(request)
    rabbitmq_url = settings.get('max_rabbitmq', None)

    # If rabbitmq_url is not defined, then we assume that we are on tests and do nothing
    if rabbitmq_url:
        server = RabbitClient(rabbitmq_url)
        # Send a conversation creation notification to rabbit
        message = RabbitMessage()
        message.prepare(settings['max_message_defaults'])
        message.update({
            "user": {
                'username': request.actor.username,
                'displayname': request.actor.displayName,
            },
            "action": "add",
            "object": "activity",
            "data": {
                'text': activity['object']['content']
            }
        })
        server.send('activity', json.dumps(message.packed), activity['contexts'][0]['hash'])
        server.disconnect()


def addConversationExchange(conversation):
    request = get_current_request()
    settings = getMAXSettings(request)
    rabbitmq_url = settings.get('max_rabbitmq', None)

    # If rabbitmq_url is not defined, then we assume that we are on tests and do nothing
    if rabbitmq_url:
        server = RabbitClient(rabbitmq_url)
        conversation_id = conversation.getIdentifier()
        participants_usernames = [user['username'] for user in conversation['participants']]
        server.conversations.create(conversation_id, users=participants_usernames)

        # Send a conversation creation notification to rabbit
        message = RabbitMessage()
        message.prepare(settings['max_message_defaults'])
        message.update({
            "user": request.actor.username,
            "action": "add",
            "object": "conversation",
            "data": {}
        })
        server.send('conversations', json.dumps(message.packed), routing_key=conversation_id)
        server.disconnect()
