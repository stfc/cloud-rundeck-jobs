import sys
import argparse
import json
from configparser import ConfigParser
import pika
from pika.exchange_type import ExchangeType
import openstack
from utils.MessageCreator import MessageCreator
CONFIG_FILE_PATH = "/etc/rabbitmq-utils/HypervisorConfig.ini"
#RecoverVM.py [ServerList] [Reboot]/[Shutdown]/[Delete]

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="VM Recovery")
    parser.add_argument("--using-ids", action="store_true", default=False)
    parser.add_argument("server_list", help="Name/IDs of server(s) to recover",
    nargs="+")

    subparser = parser.add_subparsers(dest="recovery_type", help="recovery options")

    parser_reboot = subparser.add_parser("reboot", help="reboot VM")
    parser_reboot.add_argument("--type", nargs=1,
    choices=["hard", "soft"], default="soft")

    parser_shutdown = subparser.add_parser("shutdown", help="shutdown VM")

    parser_delete = subparser.add_parser("delete", help="delete VM")
    parser_delete.add_argument("--type", nargs=1,
    choices=["hard","soft"], default="soft")

    args = parser.parse_args()
    print(args)
    try:
        #read the config file
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
        print("Unable to read config file")
        print(repr(e))
        sys.exit(1)

    try:
        conn = openstack.connect(cloud=CLOUD_NAME, region_name=REGION)
        message_creator = MessageCreator(conn)
    except Exception as e:
        print("could not establish openstack connection")
        print(repr(e))
        sys.exit(1)

    for item in args.server_list:
        if args.recovery_type == "reboot":
            message_type = "REBOOT_"+(args.type).upper()
        elif args.recovery_type == "shutdown":
            message_type = "SHUTDOWN"
        elif args.recovery_type == "delete":
            message_type = "DELETE_"+(args.type).upper()

        message = message_creator.createServerStatusMessage(message_type, ("id" if args.using_ids else "name"), item)

        if message:
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
                syslog(LOG_ERR, 'Error connecting to RabbitMQ server:')
                syslog(LOG_ERR, repr(e))
                sys.exit(1)

            print(" [*] Running {0} on server with {1} : {2}".format(message_type, "ID" if args.using_ids else "Name", item))
            print(message)
            channel.basic_publish(exchange=EXCHANGE_TYPE, routing_key=ROUTING_KEY,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2))
