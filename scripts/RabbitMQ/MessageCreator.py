import os
import datetime, openstack

class MessageCreator:
    def __init__(self, conn):
        """constructor"""
        self.conn = conn
        self.message = None

    def createMessage(self, message_type, message_dict):
        """create a message dict"""
        return {
                    "metadata": self.createMetadata(message_type),
                    "message": message_dict
                }

    def createMetadata(self, message_type):
        """create a message metadata - given a message message_type"""
        return  {
                     "timestamp": datetime.datetime.now().timestamp(),
                     "message_type": message_type
                }

    def createRebootMessage(self, host_name, package_filepath):
        """create a reboot message for a hypervisor"""
        host = self.conn.compute.find_hypervisor(host_name)
        if host:
            # read reboot packages file
            pkgs = []
            if os.path.isfile(package_filepath):
                with open(package_filepath) as f:
                    pkgs = f.readlines()
                pkgs = [x.strip() for x in pkgs]

            return self.createMessage("REQUEST_REBOOT",
            {
                "host_name": host_name,
                "packages": pkgs
            })
        return None

    def scheduleDowntimeMessage(self, host_name, duration=300, time_offset_seconds=60, author="test", comment="testing Icinga API calls", is_flexible=False):
        """ create message to shedule downtime """
        host = self.conn.compute.find_hypervisor(host_name)
        start_time = (datetime.datetime.now() + datetime.timedelta(seconds=time_offset_seconds)).timestamp()
        end_time = (start_time + duration)
        if host:
            return self.createMessage("SCHEDULE_DOWNTIME",
                {
                    "host_name": host_name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "author": author,
                    "comment": comment,
                    "is_flexible": is_flexible,
                    "flexible_duration": duration
                })
        print("host not found")
        return None

    def removeDowntimeMessage(self, host_name):
        """ create message to remove downtime """
        if self.conn.compute.find_hypervisor(host_name):
            return self.createMessage("REMOVE_DOWNTIME",
            {
                "host_name":host_name
            })
        print("host not found")
        return

    def disableServiceMessage(self, host_name, service_name="nova-compute", reason="vgc59244-admin: disabled for testing purposes"):
        """ create message to disable a service on a specified hypervisor """
        host = self.conn.compute.find_hypervisor(host_name)
        service = self.conn.compute.find_service(service_name, host=host_name)
        if host and service:
            return self.createMessage("DISABLE_SERVICE",
            {
                "host_name":host_name,
                "service_binary":service_name,
                "reason":reason
            })
        print("service and/or host not found")
        return

    def enableServiceMessage(self, host_name, service_name="nova-compute"):
        """ create message to enable a service on a specified hypervisor """
        host = self.conn.compute.find_hypervisor(host_name)
        service = self.conn.compute.find_service(service_name, host=host_name)
        if host and service:
            return self.createMessage("ENABLE_SERVICE", {
                "host_name":host_name,
                "service_binary":service_name
            })
        print("service and/or host not found")
        return

    def createVMMessage(self, server_name, image_name, flavor_name, network_name=None, zone_name=None, host_name=None):
        """ create message to create a VM/server """
        image = self.conn.compute.find_image(image_name)
        flavor = self.conn.compute.find_flavor(flavor_name)
        network = None

        if network_name:
            network = self.conn.network.find_network(network_name)
        if host_name:
            host = self.conn.compute.find_hypervisor(host_name)
        if zone_name:
            zone = self.conn.compute.get_zone(zone_name)

        if server_name and image and flavor:
            return self.createMessage("CREATE_VM",  {
                "name": server_name,
                "image_id": image["id"],
                "flavor_id": flavor["id"],
                "network_id": (network["id"] if network else None),
                "host_name": (host_name if host else None),
                "zone_name": (zone_name if zone else None)
            })

    def serverStatusMessage(self, server_name, new_status):
        """ create a message that manipulates a specified server """
        if self.conn.find_server(server_name):
            message_dict = {"name": server_name}
            return {
                "SHUTDOWN": self.createMessage("SHUTDOWN_SERVER", message_dict),
                "PAUSE" :   self.createMessage("PAUSE_SERVER", message_dict),
                "UNPAUSE" : self.createMessage("UNPAUSE_SERVER", message_dict),
                "SUSPEND" : self.createMessage("SUSPEND_SERVER", message_dict),
                "REBOOT" : self.createMessage("REBOOT_SERVER", message_dict),
                "DELETE" : self.createMessage("DELETE_SERVER", message_dict)
            }.get(new_status.upper(), None)

        print("server does not exist")
        return
