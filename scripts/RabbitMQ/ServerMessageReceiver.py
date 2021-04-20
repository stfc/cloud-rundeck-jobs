
class ServerMessageReceiver(MessageReceiver):
    """ class to handle receiving and validating a message dealing with VMs from a rabbitmq queue """
    def __init__(self, conn):
        super().__init__(conn)

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
            "SHUTDOWN_SERVER":  lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body, conn.compute.stop_server),

            "PAUSE_SERVER":     lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body, conn.compute.pause_server),

            "UNPAUSE_SERVER":   lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body, conn.compute.unpause_server),

            "SUSPEND_SERVER":   lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body, conn.compute.suspend_server),

            "RESUME_SERVER":  lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body, conn.compute.resume_server),

            "REBOOT_SERVER_SOFT":    lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body, lambda a: conn.compute.reboot_server(a, "SOFT")),

            "REBOOT_SERVER_HARD":    lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body, lambda a: conn.compute.reboot_server(a, "HARD")),

            "DELETE_SERVER":    lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body, conn.compute.delete_server),

            "LOCK_SERVER":  lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body, conn.compute.lock_server),

            "UNLOCK_SERVER":  lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body, conn.compute.lock_server),
        }.get(func_type, None)

        if helper_func:
            helper_func(ch, method, properties, body)
        else:
            #syslog(LOG_ERR, ""Could Not Read Message"")
            print("Could Not Read Message - unkown message type")

    def statusCallback(self, ch, method, properties, body, service_func):
        """Function to handle server status changes"""
        try:
            server_name = body["message"]["name"]
        except KeyError as e:
            print("error could not read message")
            print(repr(e))
            return
        server = self.conn.find_server(server_name)
        success = False
        if server:
            service_func(server)
            print("server callback handled")
            #wait to confirm handling?

        else:
            print("error server not found")

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

        if self.conn.compute.find_image(image_id) and self.conn.compute.find_flavor(flavor_id) and not self.conn.compute.find_server(name):
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
        receiver = ServiceMessageReceiver(conn)
        receiver.mainLoop()
    except KeyboardInterrupt:
        print("Interrupted")
