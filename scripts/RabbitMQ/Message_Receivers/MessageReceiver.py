import json, datetime
import pika
from pika.exchange_type import ExchangeType
import threading
import functools

class MessageReceiver:
    """
    class to handle receiving and validating a message from a rabbitmq queue.
    Base class for HostMessageReceiver and ServerMessageReceiver

    Attributes
    ----------
    conn (openstack.connection.Connection object):
        openstack connection object

    channel (pika.connection object):
        rabbitmq connection object

    Methods
    --------
    createReplyMessage(message_type, succeeded_flag, reason):
        Creates a reply message
        returns (dict) containing information to reply back to the sender

    onCallback(ch, method, properties, body, args):
        Callback function called when a message is received
        spins up a threads to handle executing message tasks
        returns None

    onMessageReceived(rabbit_conn, ch, method, properties, body):
        Validates and executes message tasks
        returns None

    sendAckMessage(ch, method):
        Sends acknowledge back to rabbitmq queue to keep channel alive whilst
        executing tasks
        returns None

    sendNotification(notif_dict, message):
        Sends a notification to user based on message parameters
        returns None

    replyToMessage(ch, method, properties, reply_body):
        Sends reply back to server
        returns None
    """
    def __init__(self, conn, host, port, queue, exchange_type, routing_key="standard_key"):
        """
        constructor class - setup rabbitmq queue and listen for messages
        Parameters:
            host (string): rabbit queue host ip
            port (int): rabbit queue port
            queue (string): name of rabbit queue
            exchange_type (string): name of rabbit exchange
        """
        self.conn = conn
        try:
            #Setup RabbitMQ Queue if not already existing
            connection_params = pika.ConnectionParameters(host=host,
            port=port, connection_attempts=10, retry_delay=2, heartbeat=5)
            connection = pika.BlockingConnection(connection_params)

            self.channel = connection.channel()
            self.channel.exchange_declare(
                 exchange="test_exchange",
                exchange_type=ExchangeType.direct,
                passive=False,
                durable=True,
                auto_delete=False
            )
            self.channel.queue_declare(queue=queue, auto_delete=False)
            self.channel.queue_bind(queue=queue, exchange="test_exchange", routing_key=routing_key)
            self.channel.basic_qos(prefetch_count=1)
        except (pika.exceptions.AMQPError, pika.exceptions.ChannelError) as e:
            print("error - unable to establish connection")
            print(repr(e))
        threads = []
        callback_func = functools.partial(self.onCallback, args=(connection, threads))
        self.channel.basic_consume(queue=queue, on_message_callback=callback_func)

        try:
            print(' [*] Waiting for messages. To exit press CTRL+C')
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
        #Stop all threads
        for thread in threads:
            thread.join()
        connection.close()

    def createReplyMessage(self, message_type, succeeded_flag, reason):
        """
        Create reply message
        Parameters:
            message_type (string): Message type recieved to reply to
            succeeded_flag (bool): If tasks related to the message completed
            successfully or not
            reason (string): specific failure/success information
        Returns:
            nested dict {metadata:{}, message:{}}: reply rabbitmq message payload
        """
        return {
                    "metadata":
                    {
                         "timestamp": datetime.datetime.now().timestamp(),
                         "message_type_received": message_type
                    },
                    "message":
                    {
                        "succeeded": succeeded_flag,
                        "reason": reason
                    }
                }

    def onCallback(self, ch, method, properties, body, args):
        (rabbit_conn, threads) = args
        t = threading.Thread(target=self.onMessageReceived, args=(rabbit_conn, ch,
        method, properties, body))
        t.start()
        threads.append(t)

    def onMessageReceived(self, rabbit_conn, ch, method, properties, body):
        """
        Callback function called when a message is recieved
        Parameters:
            rabbit_conn: rabbitmq connection object
            ch : rabbitmq channel information
            method : rabbitmq delivery method information
            properties: rabbitmq message properties
            body: message payload
        Returns: None
        """
        body = json.loads(body.decode())
        print(" [X] Recieved {}".format(body))

        cb = functools.partial(self.sendAckMessage, ch, method)
        rabbit_conn.add_callback_threadsafe(cb)

        try:
            func_type = body["metadata"]["message_type"]
            reply_required = body["metadata"]["reply_required"]
            notification_required = body["metadata"]["notification_required"]
            time_sent = body["metadata"]["timestamp"]
        except KeyError as e:
            print("Could Not Read Message - Metadata Malformed")
            print(repr(e))
            return

        helper_func = self.getHelperFunc(func_type)
        if helper_func:
            print("Performing Action...")
            succeeded_flag, reason = helper_func(ch, method, properties, body)
        else:
            print("Could Not Read Message - unkown message message_type")
            succeeded_flag = False
            reason = "Malformed Message"

        print("Finished: Status {0}, reason {1}".format(succeeded_flag, reason))

        if reply_required:
            reply = self.createReplyMessage(func_type+"_REPLY", succeeded_flag, reason)
            self.replyToMessage(ch, method, properties, reply)

        if notification_required:
            notif_dict = body["metadata"]["notification_params"]
            message = """\
            Automated Notification:
            Message: {0} Recieved - sent at {1}
            Outcome: {2}, Reason: {3}
            """.format(func_type, body["metadata"]["timestamp"], succeeded_flag, reason)
            self.sendNotification(notif_dict, message )

    def sendAckMessage(self, ch, method):
        """
        Function to send acknowledge message to keep rabbitmq channel active
        whilst tasks execute
        Parameters:
            ch : rabbitmq channel information
            method : rabbitmq delivery method information
        Returns: None
        """
        if ch.is_open:
            print("sending ack")
            ch.basic_ack(method.delivery_tag)
        else:
            print("closed")

    def sendNotification(notif_dict, message):
        """
        Function to send notifications/emails based on message parameters
        Parameters:
            notif_dict {dict}: dictionary of notification parameters outlining
            how to send notification and what content to provide
            message {dict}: message payload
        Returns: None

        NOT IMPLEMENTED
        """
        print("NOT IMPLEMENTED - SEND NOTIFICATION")
        print(notif_dict)
        #notif_dict - email_address, password?, message_header etc?
        print(message)

    def replyToMessage(self, ch, method, properties, reply_body):
        """
        Function to send reply to sender
        Parameters:
            ch : rabbitmq channel information
            method : rabbitmq delivery method information
            properties: rabbitmq message properties
            reply_body: reply message payload
        Returns: None
        """
        ch.basic_publish('', routing_key=properties.reply_to, body=json.dumps(reply_body))
