import sys
import os.path
import json
import datetime
from configparser import ConfigParser
import pika
import openstack
from pika.exchange_type import ExchangeType
from utils.MessageCreator import MessageCreator
CONFIG_FILE_PATH = "/etc/rabbitmq-utils/HypervisorConfig.ini"


if __name__ == "__main__":
    RABBIT_PORT = 5672
    RABBIT_HOST = "localhost"
    EXCHANGE_NAME = "test_exchange"
    QUEUE = "test_queue"
    ROUTING_KEY = "test_routing_key"

    CLOUD_NAME = "openstack"
    REGION = "RegionOne"
    #hostname
    try:
        #setup connection to rabbitmq queue
        connection_params = pika.ConnectionParameters(host=RABBIT_HOST,
        port=RABBIT_PORT, connection_attempts=10, retry_delay=2)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type=ExchangeType.direct,
            passive=False,
            durable=True,
            auto_delete=False
        )
        channel.queue_declare(queue=QUEUE, auto_delete=False)

    except (pika.exceptions.AMQPError, pika.exceptions.ChannelError) as e:
        print('Error connecting to RabbitMQ server:')
        print(repr(e))
        sys.exit(1)

    try:
        conn = openstack.connect(cloud=CLOUD_NAME, region_name=REGION)
        message_creator = MessageCreator(conn)
    except Exception as e:
        print("could not establish openstack connection")
        print(repr(e))
        sys.exit(1)

    print(" [*] Waking up")
    #name = open(HOSTNAME_PATH).read().strip()
    """TEST SECTION"""
    name = "hv41.nubes.rl.ac.uk"

    enable_service_message = message_creator.enableServiceMessage(name, service_name="nova-compute")
    remove_downtime_message = message_creator.removeDowntimeMessage(name)

    #remove reboot required file

    if enable_service_message and remove_downtime_message:
        print(" [*] Enabling Host")
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=ROUTING_KEY, body=json.dumps(enable_service_message),
        properties=pika.BasicProperties(delivery_mode=2))
        print(" [*] Removing Downtime")
        channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=ROUTING_KEY, body=json.dumps(remove_downtime_message),
        properties=pika.BasicProperties(delivery_mode=2))
