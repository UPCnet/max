# -*- coding: utf-8 -*-
from max.resources import getMAXSettings
from pyramid.threadlocal import get_current_request

import pika
import json


def restartTweety():
    settings = getMAXSettings(get_current_request())
    rabbitmq_url = settings.get('max_rabbitmq', None)
    # If pika_parameters is not defined, then we assume that we are on tests
    if rabbitmq_url:
        connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        channel = connection.channel()
        channel.basic_publish(exchange='',
                          routing_key='tweety_restart',
                          body='')


def messageNotification(message):
    settings = getMAXSettings(get_current_request())
    rabbitmq_url = settings.get('max_rabbitmq', None)
    maxserver_id = settings.get('max_server_id', '')

    # If talk server is not defined, then we assume that we are on tests
    if rabbitmq_url:
        conversation_id = message['contexts'][0]['id']
        username = message['actor']['username']
        displayName = message['actor']['displayName']
        text = message['object']['content']
        message_id = message['_id']

        message = {
            'conversation': conversation_id,
            'message': text,
            'username': username,
            'displayName': displayName,
            'messageID': message_id,
            'server_id': maxserver_id
        }
        connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        channel = connection.channel()
        channel.basic_publish(
            exchange=conversation_id,
            routing_key='',
            body=json.dumps(message)
        )


def addConversationExchange(conversation):
    settings = getMAXSettings(get_current_request())
    rabbitmq_url = settings.get('max_rabbitmq', None)
    # If pika_parameters is not defined, then we assume that we are on tests
    if rabbitmq_url:
        connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        channel = connection.channel()
        channel.exchange_declare(exchange=conversation.getIdentifier(),
                                 durable=True,
                                 type='fanout')
        # For binding push feature
        channel.queue_bind(exchange=conversation.getIdentifier(), queue="push")

        message = {
            'conversation': conversation.getIdentifier()
        }

        for username in conversation.participants:
            if username != conversation._owner:
                channel.basic_publish(
                    exchange='new',
                    routing_key=username,
                    body=json.dumps(message)
                )
