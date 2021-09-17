import pika
import json
import pickle
import eventlet
from st2reactor.sensor.base import Sensor
from pika.exchange_type import ExchangeType
import threading
import functools

class RabbitSensor(Sensor):
    """
    Sensor which monitors a RabbitMQ queue for new messages
    A sensor which consumes from a RabbitMQ queue, each message received will be
    dispatched to stackstorm as a `rabbitmq-new_message` TriggerInstance
    """
    def __init__(self, sensor_service, config=None):
        """
        Constructor Class
        :param sensor_service: provides utilities like
            - get_logger() - returns logger instance for the sensor
            - dispatch() for dispatching triggers to the system

        :param config: contains parsed configuration specified in config.yaml for pack
        """
        # TODO: Consume from multiple queues
        super(RabbitSensor, self).__init__(sensor_service=sensor_service, config=config)

        # setup logger
        self._logger = self._sensor_service.get_logger(name=self.__class__.__name__)

        # get sensor config info from config.yaml
        # setup config information as attributes
        self.host = self._config["rabbit_config"]["host"]
        self.port = self._config["rabbit_config"]["port"]
        self.queue = self._config["rabbit_config"]["queue"]
        self.username = self._config["rabbit_config"]["username"]
        self.password = self._config["rabbit_config"]["password"]
        self.exchange = self._config["rabbit_config"]["exchange"]
        self.exchange_durable = self._config["rabbit_config"]["exchange_durable"]
        self.routing_key = self._config["rabbit_config"]["routing_key"]

        self.rabbit_conn = None
        self.channel = None
        self.threads = []

    def setup(self):
        """
        Setup sensor - called once.
        Set up to consume messages from rabbit queue
        :return: None
        """
        # if credentials are specified
        if self.username and self.password:
            credentials = pika.credentials.PlainCredentials(username=self.username, password=self.password)
            connection_params = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                connection_attempts=10,
                retry_delay=2,
                heartbeat=5
            )
        else:
            connection_params = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                connection_attempts=10,
                retry_delay=2,
                heartbeat=5
            )

        # setup consume on rabbitmq queue
        self.rabbit_conn = pika.BlockingConnection(connection_params)
        self.channel = self.rabbit_conn.channel()

        # setup exchange
        self.channel.exchange_declare(
            exchange=self.exchange,
            exchange_type=ExchangeType.direct,
            passive=False,
            durable=self.exchange_durable,
            auto_delete=False
        )

        # setup queue
        self.channel.queue_declare(queue=self.queue, auto_delete=False)
        self.channel.queue_bind(queue=self.queue, exchange=self.exchange, routing_key=self.routing_key)
        self.channel.basic_qos(prefetch_count=1)

        # setup consume

        callback_func = functools.partial(self.on_callback, args=(self.rabbit_conn, self.threads))
        self.channel.basic_consume(queue=self.queue, on_message_callback=callback_func)

    def on_callback(self, ch, method, properties, body, args):
        """
        callback when receive a message
        :param ch: rabbitmq channel information
        :param method: rabbitmq delivery method information
        :param properties: rabbitmq message properties
        :param body: message payload
        :param args: (rabbit connection object, thread list)
        :return:
        """
        # create thread
        (rabbit_conn, threads) = args
        t = threading.Thread(target=self._dispatch_trigger, args=(rabbit_conn,
                                                                  ch,
                                                                  method,
                                                                  properties,
                                                                  body))
        #start thread and add to current thread list
        t.start()
        threads.append(t)

    def _dispatch_trigger(self, rabbit_conn, ch, method, properties, body):
        """
        Dispatches a trigger to StackStorm to handle rabbitmq message
        :param rabbit_conn: rabbitmq connection arguments
        :param ch: rabbitmq channel information
        :param method: rabbitmq delivery method information
        :param properties: rabbitmq message properties
        :param body: message payload
        :return: None
        """
        body = json.loads(body.decode())
        if not body:
            self._logger.debug("Body of message cannot be deserialized")
            return

        self._logger.debug("[X] Received message {0}".format(body))

        # send ack
        cb = functools.partial(self._send_ack, ch, method)
        rabbit_conn.add_callback_threadsafe(cb)

        """ Payload of Rabbit Message has format:
            
            metadata: 
                message_type    # determine how message handled
                
            message:
                arg1:val        # arguments for action to be run
                arg2:val
                etc
        """
        # dispatch trigger rabbitmq.openstack
        type = body["metadata"]["message_type"]

        # TODO find if reply requested

        # if direct reply requested - reply back on default exchange
        payload = {
            "routing_key": properties.reply_to,
            "message_type": type,
            "message": body["message"]}
        try:
            self._sensor_service.dispatch(trigger="stackstorm_send_notifications.rabbitmq_new_message", payload=payload)
        except Exception as e:
            self._logger.debug("Dispatch Failed, {}".format(e))

    def _send_ack(self, ch, method):
        """
        send ack to keep channel open
        :param ch: rabbitmq channel
        :param method: rabbitmq method
        :return: None
        """
        if ch.is_open:
            print("sending ack")
            ch.basic_ack(method.delivery_tag)
        else:
            print("closed")

    def run(self):
        """
        Called once after setup - continual loop
        :return: None
        """
        # called once, continual loop
        self._logger.info("Starting to consume messages from RabbitMQ for {}".format(self.queue))

        try:
            self._logger.info(" [*] Waiting for messages. To exit press CTRL+C")
            self.channel.start_consuming()
        except Exception as e:
            self.channel.stop_consuming()

    def cleanup(self):
        # called when the st2 system goes down

        # Stop all threads
        for thread in self.threads:
            thread.join()

        # close connection
        if self.rabbit_conn:
            self.rabbit_conn.close()

    def add_trigger(self, trigger):
        # method called when trigger is created
        pass

    def update_trigger(self, trigger):
        # method called when trigger is updated
        pass

    def remove_trigger(self, trigger):
        # method called when trigger is deleted
        pass
