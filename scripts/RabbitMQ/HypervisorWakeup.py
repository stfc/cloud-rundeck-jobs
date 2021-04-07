from configparser import ConfigParser
from syslog import syslog, LOG_ERR, LOG_INFO
import os.path
import json, datetime, pika, sys
from MessageCreator import MessageCreator
CONFIG_FILE_PATH = "/etc/rabbitmq-utils/HypervisorConfig.ini"


if __name__ == "__main__":
    try:
        #read the config file
        configparser = ConfigParser()
        configparser.read(CONFIG_FILE_PATH)

        RABBIT_PORT = configparser.get("global", "RABBIT_PORT")
        RABBIT_HOST = configparser.get("global", "RABBIT_HOST")

        HOSTNAME_PATH = configparser.get("local", "HOSTNAME_PATH")

        QUEUE = configparser.get("global", "QUEUE")

        CLOUD_NAME = configparser.get("openstack", "CLOUD_NAME")
        REGION = configparser.get("openstack", "REGION")
    except:
        #syslog(LOG_ERR, "Unable to read config file")
        #syslog(LOG_ERR, repr(e))
        print("error - unable to read config file")
        sys.exit(1)

    try:
        #setup connection to rabbitmq queue
        connection_params = pika.ConnectionParameters(host=RABBIT_HOST,
        port=RABBIT_PORT, connection_attempts=10, retry_delay=2)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE, durable=True)

    except (pika.exceptions.AMQPError, pika.exceptions.ChannelError) as e:
        syslog(LOG_ERR, 'Error connecting to RabbitMQ server:')
        syslog(LOG_ERR, repr(e))
        sys.exit(1)

    try:
        #setup connection with openstack
        conn = openstack.connect(cloud=CLOUD_NAME, region_name=REGION)
        message_creator = MessageCreator(conn)
    except Exception as e:
        print("could not establish openstack connection")
        print(repr(e))
        sys.exit(1)

    print(" [*] Waking up")
    name = open(HOSTNAME_PATH).read().strip()
    enable_service_message = message_creator.enableServiceMessage(name, service_name="nova-compute")
    remove_downtime_message = message_creator.removeDowntimeMessage(name)

    if enable_service_message and remove_downtime_message:
        print(" [*] Enabling Host")
        channel.basic_publish(exchange="", routing_key=QUEUE, body=json.dumps(enable_service_message),
        properties=pika.BasicProperties(delivery_mode=2))
        print(" [*] Removing Downtime")
        channel.basic_publish(exchange="", routing_key=QUEUE, body=json.dumps(remove_downtime_message),
        properties=pika.BasicProperties(delivery_mode=2))
