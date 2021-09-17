import json
import pika
from pika.credentials import PlainCredentials
from pika.exchange_type import ExchangeType
import eventlet

from st2reactor.sensor.base import Sensor

class RabbitSensor(Sensor):

    def __init__(self, sensor_service, config=None):
        super(RabbitSensor, self).__init__(sensor_service=sensor_service, config=config)

        self._logger = self._sensor_service.get_logger(name=self.__class__.__name__)

        self.host = self._config["rabbit_config"]["host"]
        self.port = self._config["rabbit_config"]["port"]
        self.queue = self._config["rabbit_config"]["queue"]
        self.username = self._config["rabbit_config"]["username"]
        self.password = self._config["rabbit_config"]["password"]
        self.exchange = self._config["rabbit_config"]["exchange"]
        self.exchange_durable = self._config["rabbit_config"]["exchange_durable"]
        self.routing_key = self._config["rabbit_config"]["routing_key"]

        self.conn = None
        self.channel = None

    def run(self):
        self._logger.info('Starting to consume messages from RabbitMQ %s', self.queue)
        # run in an eventlet in-order to yield correctly
        gt = eventlet.spawn(self.channel.start_consuming)
        # wait else the sensor will quit
        gt.wait()

    def cleanup(self):
        if self.conn:
            self.conn.close()

    def on_callback(self, ch, method, properties, body):
        body = json.loads(body.decode())

        self._logger.info("ch {0}".format(ch))

        if not body:
            self._logger.info("Body of message cannot be deserialized")
            return
        self._logger.info("[X] Received message {0}".format(body))

        if body["metadata"]["reply_required"]:

            payload = {
                "routing_key": properties.reply_to,
                "message_type": body["metadata"]["message_type"],
                "args": body["message"]
            }

            try:
                self._sensor_service.dispatch(trigger="stackstorm_send_notifications.rabbit_reply_message", payload=payload)
            finally:
                self.channel.basic_ack(delivery_tag=method.delivery_tag)
        else:

            payload = {
                "message_type": body["metadata"]["message_type"],
                "args": body["message"]
            }

            try:
                self._sensor_service.dispatch(trigger="stackstorm_send_notifications.rabbit_message",
                                              payload=payload)
            finally:
                self.channel.basic_ack(delivery_tag=method.delivery_tag)


    def setup(self):
        if self.username and self.password:
            credentials = PlainCredentials(username=self.username, password=self.password)
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
        self.channel.basic_consume(self.queue, self.on_callback)

    def update_trigger(self, trigger):
        pass

    def add_trigger(self, trigger):
        pass

    def remove_trigger(self, trigger):
        pass
