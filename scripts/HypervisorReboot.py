from configparser import ConfigParser
from syslog import syslog, LOG_ERR, LOG_INFO
import os.path
import json, datetime, pika, sys
import psutil
from MessageCreator import MessageCreator
CONFIG_FILE_PATH = "/etc/rabbitmq-utils/HypervisorConfig.ini"
REBOOT_FLAG = 0
DAYS_REQUIRED_BEFORE_CHECK = 60

def CreateRebootMessage():
    """function to send reboot message to the rabbitmq queue"""


    message_json = json.dumps(message_body)
    return message_json

def OnRebootReply(ch, method, properties, body):
    """callback function on receiving a reply from worker"""
    body = json.loads(body.decode())
    print(" [X] Recieved {}".format(body))

    if body["message"]["reboot_reply"]:
        #set reboot flag as permitted
        print("Reboot Permitted")
        REBOOT_FLAG = 1
    else:
        print("Reboot Denied")
    ch.close()
    return

def RebootCheckRequired(days_required):
    last_reboot_date = datetime.datetime.fromtimestamp(psutil.boot_time())
    threshold_date = datetime.datetime.now() - datetime.timedelta(days=days_required)
    return last_reboot_date < threshold_date

if __name__ == '__main__':

    try:
        #read the config file
        configparser = ConfigParser()
        configparser.read(CONFIG_FILE_PATH)

        RABBIT_PORT = configparser.get("global", "RABBIT_PORT")
        RABBIT_HOST = configparser.get("global", "RABBIT_HOST")
        QUEUE = configparser.get("global", "QUEUE")

        REBOOT_FILE_PATH = configparser.get("reboothypervisor", "REBOOT_FILE_PATH")
        PKG_FILE_PATH = configparser.get("reboothypervisor", "PKG_FILE_PATH")

        HOSTNAME_PATH = configparser.get("local", "HOSTNAME_PATH")

    except Exception as e:
        #syslog(LOG_ERR, "Unable to read config file")
        #syslog(LOG_ERR, repr(e))
        print("Unable to read config file")
        print(repr(e))
        sys.exit(1)

    try:
        #setup connection to rabbitmq queue
        connection_params = pika.ConnectionParameters(host=RABBIT_HOST,
        port=RABBIT_PORT, connection_attempts=10, retry_delay=2)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE, durable=True)

    except (pika.exceptions.AMQPError, pika.exceptions.ChannelError) as e:
        #syslog(LOG_ERR, 'Error connecting to RabbitMQ server:')
        #syslog(LOG_ERR, repr(e))
        print('Error connecting to RabbitMQ server:')
        print(repr(e))
        sys.exit(1)

        # if a server has run longer than DAYS_REQUIRED_BEFORE_CHECK
        # and reboot required file exits - start reboot process
    if RebootCheckRequired(DAYS_REQUIRED_BEFORE_CHECK) and os.path.isfile(REBOOT_FILE_PATH):
        host_name = open(HOSTNAME_PATH).read().strip()
        message = message_creator.createRebootMessage(host_name, PKG_FILE_PATH)
        if message:
            channel.basic_consume('amq.rabbitmq.reply-to',
                          OnRebootReply,
                          auto_ack=True)

            print(" [*] Sending Reboot Request")
            channel.basic_publish(exchange="", routing_key=QUEUE, body=message,
            properties=pika.BasicProperties(reply_to='amq.rabbitmq.reply-to', delivery_mode=2))

            #Block code until we get a reply or KeyboardInterrupt
            try:
                print(" [*] Waiting for reply ")
                channel.start_consuming()
            except KeyboardInterrupt:
                print(" [*] Cancelled Waiting ")

            if REBOOT_FLAG:
                print("Shutting Down")
                #disabled for testing
                #os.system("shutdown /r /t 10")
