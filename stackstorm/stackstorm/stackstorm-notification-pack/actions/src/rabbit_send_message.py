import pika
import json
from st2common.runners.base_action import Action

class RabbitSendMessage(Action):
    def run(self, host, port, username, password, exchange, exchange_type,
            exchange_durable, routing_key, message):

        credentials = pika.PlainCredentials(username, password)
        parameters = pika.ConnectionParameters(host=host, port=port, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        if exchange:
            channel.exchange_declare(exchange=exchange, exchange_type=exchange_type,
                                     durable=exchange_durable)

        channel.basic_publish(exchange=exchange, routing_key=routing_key, body=json.dumps(message))
        connection.close()
