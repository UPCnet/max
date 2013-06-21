# -*- coding: utf-8 -*-
import pika
import json


def messageNotification(message, talk_server):
    conversation_id = message['contexts'][0]['id']
    username = message['actor']['username']
    text = message['object']['content']
    message_id = message['_id']

    message = {
        'conversation': conversation_id,
        'message': text,
        'username': username,
        'messageID': message_id
    }

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=talk_server
        )
    )
    channel = connection.channel()
    channel.basic_publish(
        exchange=conversation_id,
        routing_key='',
        body=json.dumps(message)
    )


def addConversationExchange(conversation, talk_server):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=talk_server
        )
    )
    channel = connection.channel()
    channel.exchange_declare(exchange=conversation.getIdentifier(),
                             durable=True,
                             type='fanout')
    # For binding push feature
    # channel.queue_bind(exchange=conversation.getIdentifier(),queue="push")

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
