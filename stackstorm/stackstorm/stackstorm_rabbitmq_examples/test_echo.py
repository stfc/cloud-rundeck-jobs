import sys
import json
import pika
from pika.exchange_type import ExchangeType

CONFIG_FILE_PATH = "/etc/rabbitmq-utils/HypervisorConfig.ini"
REBOOT_FLAG = 0
DAYS_REQUIRED_BEFORE_CHECK = 10

def on_callback(ch, method, properties, body):

    body = json.loads(body.decode())
    print(" [X] Recieved {}".format(body))
    ch.close()

if __name__ == '__main__':

    RABBIT_PORT = 5672
    RABBIT_HOST = "localhost"
    EXCHANGE_NAME = "test_exchange"
    QUEUE = "test_queue"

    ROUTING_KEY = "test_routing_key"


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

    message = {
        "metadata": {"reply_required": True, "message_type": "TEST_ECHO"},
        "message": {"message": "Hello World"}
    }

    channel.basic_consume('amq.rabbitmq.reply-to',
                  on_callback,
                  auto_ack=True)

    print(" [*] Sending Echo Request")
    channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=ROUTING_KEY, body=json.dumps(message),
    properties=pika.BasicProperties(reply_to='amq.rabbitmq.reply-to', delivery_mode=2))

    #Block code until we get a reply or KeyboardInterrupt
    try:
        print(" [*] Waiting for reply ")
        channel.start_consuming()
    except KeyboardInterrupt:
        print(" [*] Cancelled Waiting ")
