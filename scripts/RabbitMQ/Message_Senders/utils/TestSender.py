from configparser import ConfigParser
import json, pika, sys
import argparse, openstack
from pika.exchange_type import ExchangeType
import sys

sys.path.append('../')
from MessageCreator import MessageCreator

CONFIG_FILE_PATH = "../../HypervisorConfig.ini"

if __name__ == "__main__":


    parser = argparse.ArgumentParser(description="Create stub rabbitmq messages")

    parser.add_argument("--host-name", type=str, required=True)
    parser.add_argument("--message-type", choices=["disable_service", "enable_service", "schedule_downtime", "remove_downtime"])
    #host = "hv57.nubes.rl.ac.uk"
    args = parser.parse_args()

    try:

        configparser = ConfigParser()
        configparser.read(CONFIG_FILE_PATH)

        RABBIT_PORT = configparser.get("global", "RABBIT_PORT")
        RABBIT_HOST = configparser.get("global", "RABBIT_HOST")
        EXCHANGE_TYPE = configparser.get("global", "EXCHANGE_TYPE")
        QUEUE = configparser.get("global", "QUEUE")

        ROUTING_KEY = configparser.get("servermessageconfig", "ROUTING_KEY")

        CLOUD_NAME = configparser.get("openstack", "CLOUD_NAME")
        REGION = configparser.get("openstack", "REGION")
    except Exception as e:
        print('Error reading ini file')
        print(repr(e))
        sys.exit(1)
    try:
        #setup connection to rabbitmq queue
        connection_params = pika.ConnectionParameters(host=RABBIT_HOST,
        port=RABBIT_PORT, connection_attempts=10, retry_delay=2)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.exchange_declare(
            exchange=EXCHANGE_TYPE,
            exchange_type=ExchangeType.direct,
            passive=False,
            durable=True,
            auto_delete=False
        )
        channel.queue_declare(queue=QUEUE, auto_delete=False)

    except (pika.exceptions.AMQPError, pika.exceptions.ChannelError) as e:
        print('Error connecting to RabbitMQ server')
        print(repr(e))
        sys.exit(1)

    try:
        conn = openstack.connect(cloud=CLOUD_NAME, region_name=REGION)
        message_creator = MessageCreator(conn)
    except Exception as e:
        print("could not establish openstack connection")
        print(repr(e))
        sys.exit(1)

    message_func = {
        "disable_service":lambda a: message_creator.disableServiceMessage(
                a,
                service_name="nova-compute",
                reason="vgc59244-admin: disabled for testing purposes"
        ),

        "enable_service":lambda a: message_creator.enableServiceMessage(
                a,
                service_name="nova-compute"
        ),

        "schedule_downtime":lambda a: message_creator.scheduleDowntimeMessage(
                a,
                duration=60,
                time_offset_seconds=60,
                author="vgc59244",
                comment="testing Icinga API calls",
                is_flexible=False
        ),

        "remove_downtime":message_creator.removeDowntimeMessage
    }.get(args.message_type, None)

    if message_func:
        message = message_func(args.host_name)
        if message:
            channel.basic_publish(exchange="", routing_key=QUEUE, body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2))
