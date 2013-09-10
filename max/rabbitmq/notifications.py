# -*- coding: utf-8 -*-
from max.resources import getMAXSettings
from pyramid.threadlocal import get_current_request

import pika
import json
import re


def pika_connection_params():
    settings = getMAXSettings(get_current_request())
    rabbitmq = settings.get('max_rabbitmq', None)
    if rabbitmq is None:
        return None
    host, port = re.search(r'\s*(\w+):?(\d*)\s*', rabbitmq).groups()
    params = {'host': host}
    if port:
        params['port'] = int(port)
    return params


def restartTweety():
    pika_params = pika_connection_params()
    # If pika_parameters is not defined, then we assume that we are on tests
    if pika_params:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(**pika_params)
        )
        channel = connection.channel()
        channel.basic_publish(exchange='',
                          routing_key='tweety_restart',
                          body='')


def messageNotification(message):
    settings = getMAXSettings(get_current_request())
    pika_params = pika_connection_params()
    maxserver_id = settings.get('max_server_id', '')

    # If talk server is not defined, then we assume that we are on tests
    if pika_params:
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
            pika.ConnectionParameters(**pika_params)
        )
        channel = connection.channel()
        channel.basic_publish(
            exchange=conversation_id,
            routing_key='',
            body=json.dumps(message)
        )


def addConversationExchange(conversation):
    pika_params = pika_connection_params()
    # If pika_parameters is not defined, then we assume that we are on tests
    if pika_params:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(**pika_params)
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
