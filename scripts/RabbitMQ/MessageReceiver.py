from configparser import ConfigParser
import os.path
import json, pika, datetime, sys
import openstack
import requests
import datetime
import time
import syslog

CONFIG_FILE_PATH = "/etc/rabbitmq-utils/HypervisorConfig.ini"

class MessageReceiver:
    """ class to handle receiving and validating a message from a rabbitmq queue"""
    def __init__(self, conn):
        self.conn = conn
        self.channel = self.setupChannel()

    def mainLoop(self):
        """ method that continuously reads messages from a channel"""
        if self.channel:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue=QUEUE, on_message_callback=self.onMessageReceived)
            print(' [*] Waiting for messages. To exit press CTRL+C')
            self.channel.start_consuming()

    def setupChannel(self):
        """ method to setup channel """
        try:
            connection_params = pika.ConnectionParameters(host=RABBIT_HOST,
            port=RABBIT_PORT, connection_attempts=10, retry_delay=2)
            connection = pika.BlockingConnection(connection_params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE, durable=True)
            return channel

        except (pika.exceptions.AMQPError, pika.exceptions.ChannelError) as e:
            #syslog(LOG_ERR, 'Error connecting to RabbitMQ server:')
            #syslog(LOG_ERR, repr(e))
            print("error - unable to establish connection")
            print(repr(e))
            return None

    def onMessageReceived(self, ch, method, properties, body):
        """callback function when a message is read from the queue"""
        body = json.loads(body.decode())
        print(" [X] Recieved {}".format(body))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        try:
            func_type = body["metadata"]["type"]
        except KeyError as e:
            #syslog(LOG_ERR, "Could Not Read Message")
            #syslog(LOG_ERR, repr(e))
            print("Could Not Read Message")
            print(repr(e))
            return

        # a dictionary to handle receiving a specific message type
        helper_func = {
            "REQUEST_REBOOT":   self.hostRebootCallback,
            "SCHEDULE_DOWNTIME":self.scheduleDowntimeCallback,
            "REMOVE_DOWNTIME":  self.removeDowntimeCallback,
            "CREATE_SERVER":    self.createServerCallback,

            "DISABLE_SERVICE":  lambda ch, method, properties, body:
            self.serviceCallback(ch, method, properties, body, conn.compute.disable_service),

            "ENABLE_SERVICE":   lambda ch, method, properties, body:
            self.serviceCallback(ch, method, properties, body, conn.compute.enable_service),

            "SHUTDOWN_SERVER":  lambda ch, method, properties, body:
            self.serverCallback(ch, method, properties, body, conn.compute.stop_server),

            "PAUSE_SERVER":     lambda ch, method, properties, body:
            self.serverCallback(ch, method, properties, body, conn.compute.pause_server),

            "UNPAUSE_SERVER":   lambda ch, method, properties, body:
            self.serverCallback(ch, method, properties, body, conn.compute.unpause_server),

            "SUSPEND_SERVER":   lambda ch, method, properties, body:
            self.serverCallback(ch, method, properties, body, conn.compute.suspend_server),

            "REBOOT_SERVER":    lambda ch, method, properties, body:
            self.serverCallback(ch, method, properties, body, conn.compute.reboot_server),

            "DELETE_SERVER":    lambda ch, method, properties, body:
            self.serverCallback(ch, method, properties, body, conn.compute.delete_server)
        }.get(func_type, None)

        if helper_func:
            helper_func(ch, method, properties, body)
        else:
            #syslog(LOG_ERR, ""Could Not Read Message"")
            print("Could Not Read Message - unkown message type")

    def hostRebootCallback(self, ch, method, properties, body):
        """ when message received is a REBOOT_SERVER message """
        print("TODO: NOT IMPLEMENTED - put the hypervisor appropriate downtimes")

        ch.basic_publish('', routing_key=properties.reply_to, body=json.dumps({
            "metadata": {"timestamp": datetime.datetime.now().timestamp(), "type":"REBOOT_REPLY"},
            "message" : {"reboot_reply": True}
        }))

    def getHost(self, host, url):
        """ helper function to get hypervisor info from Icinga endpoint """
        r = requests.get(url, auth=(ICINGA_API_USERNAME, ICINGA_API_PASSWORD), verify=False,
         params = {"filter":"host.name==\"{}\"".format(host)})

        if r.status_code == requests.codes.ok and len(r.json()["results"]) > 0:
            return r.json()
        else:
            return None

    def scheduleDowntimeCallback(self, ch, method, properties, body):
        """Function to request downtime on icinga"""
        """REQUIRED : author, comment, start_time, end_time, is_flexible, flexible_duration"""

        try:
            host = body["message"]["host_name"]
            start_time = body["message"]["start_time"]
            end_time = body["message"]["end_time"]
            author = body["message"]["author"]
            comment =  body["message"]["comment"]
            is_flexible = body["message"]["is_flexible"]
            flexible_duration = body["message"]["flexible_duration"]
        except KeyError as e:
            print("error could not read message")
            print(repr(e))
            return

        if self.getHost(host, ICINGA_HOSTS_ENDPOINT):
            if not end_time > start_time > datetime.datetime.now().timestamp():
                print("given scheduled dates are malformed")
                return
            r = requests.post(ICINGA_SCHEDULE_DOWNTIMES_ENDPOINT,
                              headers={"Accept":"application/json"},
                              auth=(ICINGA_API_USERNAME, ICINGA_API_PASSWORD),
                              verify=False,
                              data=json.dumps({
                                  "type":"Host",
                                  "filter": "host.name==\"{}\"".format(host),
                                  "author": author,
                                  "start_time": start_time,
                                  "end_time": end_time,
                                  "comment": comment,
                                  "all_services":1,
                                  "duration": flexible_duration if is_flexible else (end_time - start_time),
                                  "fixed": False if is_flexible else True
                              })
                             )
            if r.status_code == requests.codes.ok:
                print("downtime of host {0} scheduled for {1} until {2} (Fixed: {3}, Duration: {4})".format(
                        host,
                        datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d, %H:%M:%S'),
                        datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d, %H:%M:%S'),
                        not is_flexible,
                        duration
                    )
                )
            else:
                print("downtime could not be scheduled")
                print(r.text)

    def removeDowntimeCallback(self, ch, method, properties, body):
        """Function to remove downtime on icinga """
        try:
            host = body["message"]["host_name"]
        except KeyError as e:
            print("error could not read message")
            print(repr(e))
            return

        if self.getHost(host, ICINGA_DOWNTIMES_ENDPOINT):
            r = requests.post(ICINGA_REMOVE_DOWNTIMES_ENDPOINT,
                              headers={"Accept":"application/json"},
                              auth=(ICINGA_API_USERNAME, ICINGA_API_PASSWORD),
                              verify=False,
                              data=json.dumps({
                                  "type": "Host",
                                  "filter":"host.name==\"{}\"".format(host)
                              })
                             )
            if r.status_code == requests.codes.ok:
                print("downtime of host removed")
            else:
                print("downtime could not be removed")
                print(r.text)
        else:
            print("host not found - exiting")

    def serverCallback(self, ch, method, properties, body, service_func):
        """Function to handle server status changes"""
        try:
            server_name = body["message"]["name"]
        except KeyError as e:
            print("error could not read message")
            print(repr(e))
            return
        if self.conn.find_server(server_name):
            service_func(server_name)
            print("server callback handled")
        else:
            print("error server not found")

    def serviceCallback(self, ch, method, properties, body, service_func):
        """Function to disable/enable service"""
        try:
            host_name = body["message"]["host_name"]
            service_binary = body["message"]["service_binary"]
            if body["metadata"]["type"] == "DISABLE_SERVICE":
                reason = body["message"]["reason"]
        except KeyError as e:
            print("error could not read message")
            print(repr(e))
            return

        host = self.conn.compute.find_hypervisor(host_name)
        service = self.conn.compute.find_service(service_binary, host=host_name)
        if host and service:
            if body["metadata"]["type"] == "DISABLE_SERVICE":
                service_func(service, host_name, service_binary, reason)
            else:
                service_func(service, host_name, service_binary)
                print("service callback handled")
        else:
            print("error host and/or service not found")

    def createServerCallback(self, ch, method, properties, body):
        """Function to create server"""
        try:
            name = body["message"]["name"]
            image_id = body["message"]["image_id"]
            flavor_id = body["message"]["flavor_id"]
            network_id = body["message"]["network_id"]
            host =  body["message"]["host_name"]
            zone = body["message"]["zone_name"]
        except KeyError as e:
            print("error could not read message")
            print(repr(e))
            return

        if image and flavor and not self.conn.compute.find_server(name):
            availability_zone = None
            if host and zone:
                availability_zone = "{}:{}".format(host, zone)
            conn.compute.create_server(name, image_id, flavor_id, network_id, availability_zone)
        print("error image, flavor or server not found")
        return


if __name__ == "__main__":
    try:
        configparser = ConfigParser()
        configparser.read(CONFIG_FILE_PATH)

        RABBIT_PORT = configparser.get("global", "RABBIT_PORT")
        RABBIT_HOST = configparser.get("global", "RABBIT_HOST")
        QUEUE = configparser.get("global", "QUEUE")

        ICINGA_API_USERNAME = configparser.get("icinga", "ICINGA_API_USERNAME")
        ICINGA_API_PASSWORD = configparser.get("icinga", "ICINGA_API_PASSWORD")
        ICINGA_URL = configparser.get("icinga", "ICINGA_URL")

        ICINGA_HOSTS_ENDPOINT = configparser.get("icinga", "ICINGA_HOSTS_ENDPOINT")
        ICINGA_DOWNTIMES_ENDPOINT = configparser.get("icinga", "ICINGA_DOWNTIMES_ENDPOINT")
        ICINGA_SCHEDULE_DOWNTIMES_ENDPOINT = configparser.get("icinga", "ICINGA_SCHEDULE_DOWNTIMES_ENDPOINT")
        ICINGA_REMOVE_DOWNTIMES_ENDPOINT = configparser.get("icinga", "ICINGA_REMOVE_DOWNTIMES_ENDPOINT")

        CLOUD_NAME = configparser.get("openstack", "CLOUD_NAME")
        REGION = configparser.get("openstack", "REGION")
    except Exception as e:
        #syslog(LOG_ERR, "Unable to read config file")
        #syslog(LOG_ERR, repr(e))
        print("error - unable to read config file")
        sys.exit(1)

    try:
        conn = openstack.connect(cloud=CLOUD_NAME, region_name=REGION)
    except Exception as e:
        print("could not establish openstack connection")
        print(repr(e))
        sys.exit(1)

    try:
        receiver = MessageReceiver(conn)
        receiver.mainLoop()
    except KeyboardInterrupt:
        print("Interrupted")
