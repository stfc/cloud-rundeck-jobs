import json, datetime, sys
from configparser import ConfigParser
import pika
import openstack
import requests

CONFIG_FILE_PATH = "/etc/rabbitmq-utils/HypervisorConfig.ini"

class MessageReceiver:
    """ class to handle receiving and validating a message from a rabbitmq queue"""
    def __init__(self, conn):
        self.conn = conn
        self.channel = self.setupChannel()

    def mainLoop(self):
        """ method that continuously reads messages from a channel"""
        if self.channel:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue=QUEUE, on_message_callback=self.onMessageReceived)
            print(' [*] Waiting for messages. To exit press CTRL+C')
            self.channel.start_consuming()

    def setupChannel(self):
        """ method to setup channel """
        try:
            connection_params = pika.ConnectionParameters(host=RABBIT_HOST,
            port=RABBIT_PORT, connection_attempts=10, retry_delay=2)
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE, durable=True)
            return channel

        except (pika.exceptions.AMQPError, pika.exceptions.ChannelError) as e:
            #syslog(LOG_ERR, 'Error connecting to RabbitMQ server:')
            #syslog(LOG_ERR, repr(e))
            print("error - unable to establish connection")
            print(repr(e))
            return None

    def onMessageReceived(self):
        """callback function when a message is read from the queue"""
        body = json.loads(body.decode())
        print(" [X] Recieved {}".format(body))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        try:
            func_type = body["metadata"]["type"]
        except KeyError as e:
            #syslog(LOG_ERR, "Could Not Read Message")
            #syslog(LOG_ERR, repr(e))
            print("Could Not Read Message")
            print(repr(e))
            return
