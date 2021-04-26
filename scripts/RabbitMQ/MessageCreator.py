import os
import datetime, openstack

class MessageCreator:
    def __init__(self, cloud_name, region, reply_required=False, notification_required=False, notification_params=None):
        """constructor"""
        self.conn = openstack.connect(cloud=cloud_name, region_name=region)
        self.message = {"metadata":{
            "reply_required": reply_required,
            "notification_required": notification_required,
            "notif_params": notification_params
        }, "message":None}

    def populateMessage(self, message_type, message_dict):
        print(message_type)
        self.message["metadata"]["message_type"] = message_type
        self.message["metadata"]["timestamp"] = datetime.datetime.now().timestamp()

        self.message["message"] = message_dict
        return self.message

    def createRebootMessage(self, host_name, package_filepath):
        """create a reboot message for a hypervisor"""
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
    author="test", comment="testing Icinga API calls"):
        """ create message to shedule downtime """
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
        """ create message to remove downtime """
        if not self.conn.compute.find_hypervisor(host_name):
            print("host not found")
            return
        return self.populateMessage("REMOVE_DOWNTIME", {
            "host_name":host_name
        })

    def disableServiceMessage(self, host_name, service_name="nova-compute",
    reason="vgc59244-admin: disabled for testing purposes"):
        """ create message to disable a service on a specified hypervisor """
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
        """ create message to enable a service on a specified hypervisor """
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
        """ create message to create a VM/server """

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

    def serverStatusHelper(self, server_id, message_type):
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

    def serverStatusMessageFromID(self, server_id, message_type):
        """ create a message that manipulates a specified server given its ID """
        try:
            #return self.serverStatusHelper(
            #[server for server in self.conn.list_servers(all_projects=True) if server["id"] == server_id][0]["id"],
            #message_type)
            return self.serverStatusHelper(server_id, message_type)
        except Exception as e:
            print("Server With ID {0} Not Found".format(server_id))
            return

    def serverStatusMessageFromName(self, server_name, message_type):
        """ create a message that manipulates a specified server given its name """
        servers_matching = [server for server in self.conn.list_servers(all_projects=True) if server["name"] == server_name]
        if not servers_matching:
            print("Server Name {0} Not Found".format(server_name))
            return
        elif len(servers_matching) > 1:
            print("Multiple Servers Named {0} found - aborting".format(server_name))
            return
        return self.serverStatusHelper(servers_matching[0]["id"], message_type)
