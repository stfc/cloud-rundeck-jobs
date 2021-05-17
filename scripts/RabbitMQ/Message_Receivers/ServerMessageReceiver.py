import sys
from configparser import ConfigParser
import openstack
from MessageReceiver import MessageReceiver
CONFIG_FILE_PATH = "../HypervisorConfig.ini"

class ServerMessageReceiver(MessageReceiver):
    """
    class to handle receiving and validating a message dealing with VMs
    from a rabbitmq queue. Inherits from MessageReceiver base class

    Attributes
    ----------
    None

    Methods
    --------
    getHelperFunc(func_type):
        Overrides MessageReceiver getHelperFunc - determines how to handle a
        message, based on its message type. Calls appropriate helper function

    statusCallback(ch, method, properties, body, service_func, new_status)
        Helper function to handle server status change
        returns (Bool, String) tuple after handling message

    deleteServerCallback(ch, method, properties, body, hard_delete=False)
        Helper function to handle server deletion
        returns (Bool, String) tuple after handling message

    createServerCallback(ch, method, properties, body)
        Helper function to handle server creation
        returns (Bool, String) tuple after handling message
    """
    def getHelperFunc(self, func_type):
        """
        Function to get Callback Function For Corresponding Message Types
            Parameters:
                func_type (string) : unique message type identifier
            Returns:
                (lambda function()) which needs to be called to handle
                that particular message
        """
        return {
            "CREATE_SERVER": self.createServerCallback,

            "SHUTDOWN_SERVER":  lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body,
            self.conn.compute.stop_server, "SHUTOFF"),

            "PAUSE_SERVER":     lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body,
            self.conn.compute.pause_server, "PAUSED"),

            "SUSPEND_SERVER":   lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body,
            self.conn.compute.suspend_server, "SUSPENDED"),

            "RESUME_SERVER":  lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body,
            self.conn.compute.resume_server, "ACTIVE"),

            "REBOOT_SERVER_SOFT":    lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body,
            lambda a: self.conn.compute.reboot_server(a, "SOFT"), "ACTIVE"),

            "REBOOT_SERVER_HARD":    lambda ch, method, properties, body:
            self.statusCallback(ch, method, properties, body,
            lambda a: self.conn.compute.reboot_server(a, "HARD"), "ACTIVE"),

            "DELETE_SERVER_HARD": lambda ch, method, properties, body:
            self.deleteServerCallback(ch, method, properties, body, hard_delete=True),

            "DELETE_SERVER_SOFT": self.deleteServerCallback

        }.get(func_type, None)

    def statusCallback(self, ch, method, properties, body, service_func, new_status):
        """
        Function called when message involves changing the state of a server
            Parameters:
                ch : rabbitmq channel information
                method : rabbitmq delivery method information
                properties: rabbitmq message properties
                body: message payload
                service_func: specific server status change message type
                new_status: what the status will be after the change
            Returns: (Bool, String): tuple after handling message - if handling
            succeeded/failed (Bool) and return message/reason failed (String)
        """
        try:
            server_id = body["message"]["id"]
        except KeyError as e:
            return (False, "Malformed Message: {0}".format(repr(e)))

        print("validating server")
        try:
            server = conn.compute.find_server(server_id)
        except Exception as e:
            return (False, "Server with ID {0} Not Found".format(server_id))
        print("finished validating server")

        try:
            host = self.conn.compute.find_hypervisor(server["hypervisor_hostname"])
        except Exception as e:
            print("Error finding host")
            host = None

        if not host:
            return (False, "Could not find Server's Host Hypervisor {0}".format(server["hypervisor_hostname"]))
        if host["status"] == "disabled":
            return (False, "Host Hypervisor {0} is disabled")

        try:
            print("performing action")
            service_func(server)

            print("waiting for server")
            if not new_status == "SHUTOFF":
                self.conn.compute.wait_for_server(server, new_status)

            return (True, "Status Change Successful")

        except Exception as e:
            return (False, "Server Status Change Failed: {0}".format(repr(e)))

    def deleteServerCallback(self, ch, method, properties, body, hard_delete=False):
        """
        Function called when message has DELETE_SERVER message_type
            Parameters:
                ch : rabbitmq channel information
                method : rabbitmq delivery method information
                properties: rabbitmq message properties
                body: message payload
                hard_delete: True: only delete SHUTOFF servers. False: delete regardless of status
            Returns: (Bool, String): tuple after handling message - if handling
            succeeded/failed (Bool) and return message/reason failed (String)
        """
        try:
            server_id = body["message"]["id"]
        except KeyError as e:
            return (False, "Malformed Message: {0}".format(repr(e)))

        print("validating server")
        try:
            server = server = conn.compute.find_server(server_id)
        except Exception as e:
            return (False, "Server with ID {0} Not Found".format(server_id))
        print("finished validating server")

        if hard_delete or server["status"] == "SHUTOFF":
            self.conn.compute.delete_server(server)
            return (True, "Server Deleted")
        else:
            return (False, "SOFT DELETE ERROR - Server Not Shutoff")

    def createServerCallback(self, ch, method, properties, body):
        """
        Function called when message has CREATE_SERVER message_type
            Parameters:
                ch : rabbitmq channel information
                method : rabbitmq delivery method information
                properties: rabbitmq message properties
                body: message payload
            Returns: (Bool, String): tuple after handling message - if handling
            succeeded/failed (Bool) and return message/reason failed (String)
        """
        try:
            name = body["message"]["name"]
            image_id = body["message"]["image_id"]
            flavor_id = body["message"]["flavor_id"]
            network_id = body["message"]["network_id"]
            host =  body["message"]["host_name"]
            zone = body["message"]["zone_name"]
        except KeyError as e:
            return (False, "Malformed Message: {0}".format(repr(e)))

        if self.conn.compute.find_image(image_id):
            return (False, "Image Not Found")

        if self.conn.compute.find_flavor(flavor_id):
            return (False, "Flavor Not Found")

        availability_zone = None
        if host and zone:
            availability_zone = "{}:{}".format(host, zone)
        try:
            self.conn.compute.create_server(name, image_id, flavor_id, network_id, availability_zone)
            return (True, "Server Creation Successful")
        except Exception as e:
            print(repr(e))
            return (False, "Openstack Error: {0}".format(repr(e)))

if __name__ == "__main__":
    try:
        configparser = ConfigParser()
        configparser.read(CONFIG_FILE_PATH)

        RABBIT_PORT = configparser.get("global", "RABBIT_PORT")
        RABBIT_HOST = configparser.get("global", "RABBIT_HOST")
        QUEUE = configparser.get("global", "QUEUE")
        EXCHANGE_TYPE = configparser.get("global", "EXCHANGE_TYPE")

        CLOUD_NAME = configparser.get("openstack", "CLOUD_NAME")
        REGION = configparser.get("openstack", "REGION")

        ROUTING_KEY = configparser.get("servermessageconfig", "ROUTING_KEY")
    except Exception as e:
        print("error - unable to read config file")
        print(repr(e))
        sys.exit(1)

    try:
        conn = openstack.connect(cloud=CLOUD_NAME, region_name=REGION)
    except Exception as e:
        print("could not establish openstack connection")
        print(repr(e))
        sys.exit(1)

    try:
        receiver = ServerMessageReceiver(conn, RABBIT_HOST, RABBIT_PORT, QUEUE, EXCHANGE_TYPE, ROUTING_KEY)
    except KeyboardInterrupt:
        print("Interrupted")
