import os.path
import sys
import json
import datetime
from configparser import ConfigParser
import psutil
import pika
import openstack
from utils.MessageCreator import MessageCreator
from pika.exchange_type import ExchangeType

CONFIG_FILE_PATH = "/etc/rabbitmq-utils/HypervisorConfig.ini"
REBOOT_FLAG = 0
DAYS_REQUIRED_BEFORE_CHECK = 10

def OnRebootReply(ch, method, properties, body):
    """
    Callback Function to handle receiving a reply from worker - sets global
    flag REBOOT_FLAG
        Parameters:
            ch : rabbitmq channel information
            method : rabbitmq delivery method information
            properties: rabbitmq message properties
            body: message payload
        Returns:
            None
    """
    global REBOOT_FLAG
    body = json.loads(body.decode())
    print(" [X] Recieved {}".format(body))

    if body["message"]["succeeded"]:
        #set reboot flag as permitted
        print("Reboot Permitted")
        REBOOT_FLAG = 1
    else:
        print("Reboot Denied")
    ch.close()

def RebootCheckRequired(days_required):
    """
    Function to check if the host has been running for long enough
    that a reboot is required
        Parameters:
            days_required(int): days running threshold for a reboot to take place
        Returns: (bool) if a reboot is required or not
    """
    last_reboot_date = datetime.datetime.fromtimestamp(psutil.boot_time())
    threshold_date = datetime.datetime.now() - datetime.timedelta(days=days_required)
    return last_reboot_date < threshold_date

if __name__ == '__main__':

    RABBIT_PORT = 5672
    RABBIT_HOST = "localhost"
    EXCHANGE_NAME = "test_exchange"
    QUEUE = "test_queue"
    ROUTING_KEY = "test_routing_key"
    #HOSTNAME = "hv41.nubes.rl.ac.uk"
    CLOUD_NAME = "openstack"
    REGION = "RegionOne"

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
        message_creator = MessageCreator(conn, reply_required=True)
    except Exception as e:
        print("could not establish openstack connection")
        print(repr(e))
        sys.exit(1)

        # if a server has run longer than DAYS_REQUIRED_BEFORE_CHECK
        # and reboot required file exits - start reboot process
    if RebootCheckRequired(DAYS_REQUIRED_BEFORE_CHECK) and os.path.isfile(REBOOT_FILE_PATH):

        #ACTUAL CODE
        #host_name = open(HOSTNAME_PATH).read().strip()
        #message = message_creator.createRebootMessage(host_name, PKG_FILE_PATH)

        #TEST SECTION - REMOVE LINE
        message = message_creator.populateMessage("REBOOT_HOST", True,
        {"host_name": "hv41.nubes.rl.ac.uk", "packages": []})

        #ACTUAL CODE
        if message:
            channel.basic_consume('amq.rabbitmq.reply-to',
                          OnRebootReply,
                          auto_ack=True)

            print(" [*] Sending Reboot Request")
            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=ROUTING_KEY, body=json.dumps(message),
            properties=pika.BasicProperties(reply_to='amq.rabbitmq.reply-to', delivery_mode=2))

            #Block code until we get a reply or KeyboardInterrupt
            try:
                print(" [*] Waiting for reply ")
                channel.start_consuming()
            except KeyboardInterrupt:
                print(" [*] Cancelled Waiting ")

            if REBOOT_FLAG:
                print("Shutting Down")

                #DISABLED FOR TESTING
                #os.system("shutdown /r /t 10")
    else:
        print("Reboot not required")
