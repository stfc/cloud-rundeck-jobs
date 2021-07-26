import os
import datetime, openstack

class MessageCreator:
    """
    class to handle receiving and validating a generic rabbitmq message. Base
    class for HostMessageReceiver and ServerMessageReceiver.

    Attributes
    ----------
    conn: (openstack.connection.Connection object)
        openstack connection object

    self.message: nested dict {metadata:{}, message:{}}:
        stores the message object

    Methods
    --------
    populateMessage(message_type, message_dict):
        method to create message given message type and message payload
        returns message body as a dict

    createRebootMessage(host_name, package_filepath):
        method to create message payload with info related to REBOOT_HOST message type
        (populates message with packages to be updated)
        returns message payload as dict

    scheduleDowntimeMessage(host_name, duration=300, time_offset_seconds=60,
    author="test", comment="testing Icinga API calls"):
        method to create message payload with info related to SCHEDULE_DOWNTIME message type
        returns message payload as dict

    removeDowntimeMessage(host_name):
        method to create message payload with info related to REMOVE_DOWNTIME  message type
        returns message payload as dict

    disableServiceMessage(host_name, service_name="nova-compute",
    reason="vgc59244-admin: disabled for testing purposes"):
        method to create message payload with info related to DISABLE_SERVICE message type
        returns message payload as dict

    enableServiceMessage(host_name, service_name="nova-compute"):
        method to create message payload with info related to ENABLE_SERVICE message type
        returns message payload as dict

    createVMMessage(server_name, image_name, flavor_name, network_name=None, zone_name=None, host_name=None):
        method to create message payload with info related to CREATE_SERVER message type
        returns message payload as dict

    createServerStatusMessage(server_id, message_type):
        method to create message payload with info related to any VM status change message types
        returns message payload as dict

    getServerFromName(server_name):
        method to return server info given the server name
        returns server info as dict or None if server with name not found
    """
    def __init__(self, conn, reply_required=False, notification_required=False, notification_params=None):
        """
        constructor class
            Parameters:
                reply_required: (bool) Default: (False)
                    set in message metadata if sender expects a reply or not

                notification_required: (bool) Default: (False)
                    set in message metadata if a notification is to be sent

                notification_params: dict Default: (None)
                    dictionary of notification_params to determin contents and procedure of
                    sending the notification
        """
        self.conn = conn
        self.message = {"metadata":{
            "reply_required": reply_required,
            "notification_required": notification_required,
            "notif_params": notification_params
        }, "message":None}

    def populateMessage(self, message_type, message_dict):
        """
        pdbopulate message dictionary attribute with a given message type and a message body dict
        Parameters:
            message_type (string): message type
            message_dict (dict): populated dictionary of info to send to worker
        Returns:
            populated self.message dictionary
        """
        print(message_type)
        self.message["metadata"]["message_type"] = message_type
        self.message["metadata"]["timestamp"] = datetime.datetime.now().timestamp()

        self.message["message"] = message_dict
        return self.message

    def createRebootMessage(self, host_name, package_filepath):
        """
        Create a REBOOT_HOST message
        Parameters:
            host_name: name of host to reboot
            package_filepath: path to file which holds package name to update
        Returns: dictionary - a populated rabbitmq message body
        """
        host = self.conn.compute.find_hypervisor(host_name)
        if not host:
            print("host not found")
            return
        # read reboot packages file
        pkgs = []
        if os.path.isfile(package_filepath):
            with open(package_filepath) as f:
                pkgs = f.readlines()
            pkgs = [x.strip() for x in pkgs]
        return self.populateMessage("REBOOT_HOST", {
            "host_name": host_name,
            "packages": pkgs
        })

    def scheduleDowntimeMessage(self, host_name, duration=300, time_offset_seconds=60,
    author="test", comment="testing Icinga API calls", is_flexible=False):
        """
        Create a SCHEDULE_DOWNTIME message
        Parameters:
            host_name: name of host to schedule downtime
            duration: number of seconds the downtime should last for
            time_offset_seconds: number of seconds to wait before downtime
            starts from when the downtime was scheduled
            author: name of user/author who scheduled the downtime
            comment: reason/comment on to display on Icinga
        Returns:
            dictionary - a populated rabbitmq message body
        """
        host = self.conn.compute.find_hypervisor(host_name)
        start_time = (datetime.datetime.now() + datetime.timedelta(seconds=time_offset_seconds)).timestamp()
        end_time = (start_time + duration)
        if not host:
            print("host not found")
            return
        return self.populateMessage("SCHEDULE_DOWNTIME", {
                "host_name": host_name,
                "start_time": start_time,
                "end_time": end_time,
                "author": author,
                "comment": comment,
                "is_flexible": is_flexible,
                "flexible_duration": duration
        })

    def removeDowntimeMessage(self, host_name):
        """
        Create a REMOVE_DOWNTIME message
        Parameters:
            host_name: name of host to remove downtime for
        Returns:
            dictionary - a populated rabbitmq message body
        """
        if not self.conn.compute.find_hypervisor(host_name):
            print("host not found")
            return
        return self.populateMessage("REMOVE_DOWNTIME", {
            "host_name":host_name
        })

    def disableServiceMessage(self, host_name, service_name="nova-compute",
    reason="vgc59244-admin: disabled for testing purposes"):
        """
        Create a DISABLE_SERVICE message
        Parameters:
            host_name: name of host running the service to be disabled
            service_binary: name of service to be disabled
            reason: reason to disable the service
        Returns:
            dictionary - a populated rabbitmq message body
        """
        host = self.conn.compute.find_hypervisor(host_name)
        service = self.conn.compute.find_service(service_name, host=host_name)
        if not host:
            print("host not found")
            return
        if not service:
            print("service not found on host")
            return
        return self.populateMessage("DISABLE_SERVICE", {
            "host_name":host_name,
            "service_binary":service_name,
            "reason":reason
        })

    def enableServiceMessage(self, host_name, service_name="nova-compute"):
        """ create message to enable a service on a specified hypervisor
        Create a ENABLE_SERVICE message
        Parameters:
            host_name: name of host running the service to be enabled
            service_name: name of service to enable
        Returns:
            dictionary - a populated rabbitmq message body
        """
        host = self.conn.compute.find_hypervisor(host_name)
        service = self.conn.compute.find_service(service_name, host=host_name)
        if not host:
            print("host not found")
            return
        if not service:
            print("service not found on host")
            return
        return self.populateMessage("ENABLE_SERVICE", {
            "host_name":host_name,
            "service_binary":service_name
        })

    def createVMMessage(self, server_name, image_name, flavor_name, network_name=None, zone_name=None, host_name=None):
        """
        create a CREATE_VM message
        Parameters:
            server_name: name of the new server
            image_name: name of image the new server will use
            flavor_name: name of the flavor the new server will use
            network_name: name of network the server will be created on
            zone_name: name of zone the server will be created on
            host_name: name of hypervisor the server will be run on
        Return:
            dictionary - a populated rabbitmq message body
        """
        image = self.conn.compute.find_image(image_name)
        if not image:
            print("image not found")
            return
        flavor = self.conn.compute.find_flavor(flavor_name)
        if not flavor:
            print("flavor not found")
            return

        if network_name:
            network = self.conn.network.find_network(network_name)
            if not network:
                print("network not found")
                return
        if host_name:
            host = self.conn.compute.find_hypervisor(host_name)
            if not host:
                print("host not found")
                return
        if zone_name:
            zone = self.conn.compute.get_zone(zone_name)
            if not zone:
                print("zone not found")
                return

        return self.populateMessage("CREATE_VM", {
            "name": server_name,
            "image_id": image["id"],
            "flavor_id": flavor["id"],
            "network_id": (network["id"] if network else None),
            "host_name": (host_name if host else None),
            "zone_name": (zone_name if zone else None)
        })

    def getServerFromName(server_name):
        """
        Helper function - search for information about a server given its name
        (must be unique)
        Parameters:
            server_name: name of server
        Returns:
            munch.Munch object: containing server information
        """
        servers_matching = [server for server in self.conn.list_servers(all_projects=True, filters={"limit":1000}) if server["name"] == server_name]
        if not servers_matching:
            print("Server Name {0} Not Found".format(server_name))
            return None
        elif len(servers_matching) > 1:
            print("Multiple Servers Named {0} found - aborting".format(server_name))
            return None
        return servers_matching[0]

    def createServerStatusMessage(self, message_type, server_identifier, value):
        """
        Create any server status change message
        Parameters:
            message_type (string): what status change to make
            server_identifier (string): an identifier to find server (name or id)
            value (string): the value for the server_identifier
        Returns:
            dictionary - a populated rabbitmq message body
        """

        if server_identifier == "id":
            server_dict = self.conn.compute.find_server(value)
        elif server_identifier == "name":
            server_dict = getServerFromName(value)
        else:
            print("Identifier not recognised")
            return

        if server_dict:
            server_id = server_dict["id"]
        else:
            print("Server with {0}: {1} not found".format(server_identifier.upper(), value))
            return

        return {
            "SHUTDOWN": lambda message: self.populateMessage("SHUTDOWN_SERVER", message),
            "PAUSE" : lambda message: self.populateMessage("PAUSE_SERVER", message),
            "SUSPEND" : lambda message: self.populateMessage("SUSPEND_SERVER", message),
            "RESUME":  lambda message: self.populateMessage("RESUME_SERVER", message),
            "REBOOT_SOFT" : lambda message: self.populateMessage("REBOOT_SERVER_SOFT", message),
            "REBOOT_HARD": lambda message: self.populateMessage("REBOOT_SERVER_HARD", message),
            "DELETE_SOFT" : lambda message: self.populateMessage("DELETE_SERVER_SOFT", message),
            "DELETE_HARD" : lambda message: self.populateMessage("DELETE_SERVER_HARD", message)
        }.get(message_type.upper(), None)({"id": server_id})
