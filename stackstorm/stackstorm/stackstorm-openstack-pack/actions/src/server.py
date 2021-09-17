from openstack_action import OpenstackAction


class Server(OpenstackAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.func = {
            "server_change_status": self.server_change_status,
            "server_update": self.server_update,
            "server_create": self.server_create,
            "server_delete": self.server_delete,
            "server_show": self.server_show,
            "server_reboot": self.server_reboot,
            "server_shutdown": self.server_shutdown,
            "server_restart": self.server_restart
        }

    def server_update(self, server, **update_kwargs):
        """
        Update properties of a server
        :param server: Name or ID
        :param update_kwargs: update properties
        :return: (status (Bool), reason (String))
        """
        raise NotImplementedError

    def server_show(self, server):
        """
        Show server properties
        :param server: Name or ID
        :return: (status (Bool), reason (String))
        """
        server_id = self.find_resource_id(server, self.conn.compute.find_server)
        if not server_id:
            return False, "Server not found with Name or ID {}".format(server)
        try:
            server = self.conn.compute.find_server(server_id)
        except Exception as e:
            return False, "Finding User Failed {}".format(e)
        return True, server

    def server_change_status(self, server, status_change):
        """
           Function called when message involves changing the status of a server
               :param: status_change: String: What status change to perform
               :param: server: String: Name or ID of Server to change status
               :returns: (status (Bool), reason (String))
        """
        server_id = self.find_resource_id(server, self.conn.compute.find_server)
        if not server_id:
            return False, "Server not found with Name or ID {}".format(server)

        hypervisor_identifier = self.conn.compute.find_server(server_id)["hypervisor_hostname"]
        hypervisor = self.conn.compute.find_hypervisor(hypervisor_identifier)
        if not hypervisor:
            return False, "Error finding hypervisor hosting server with ID {}".format(server_id)

        server_func, new_status = {
            "suspend": (self.conn.compute.suspend_server, "SUSPENDED"),
            "resume": (self.conn.compute.resume_server, "ACTIVE"),
            "restart": (self.conn.compute.start_server, "ACTIVE"),
            "shutdown": (self.conn.compute.stop_server, "SHUTOFF"),
            "reboot_soft": (lambda server: self.conn.compute.reboot_server(server, "SOFT"), "ACTIVE"),
            "reboot_hard": (lambda server: self.conn.compute.reboot_server(server, "HARD"), "ACTIVE"),
        }.get(status_change, (None, None))

        if not server_func:
            return False, "Server \"status_change\" given {0} not valid".format(status_change)
        try:
            print("Scheduling Action")
            server_func(server_id)
            print("Waiting until status change detected")
            if not new_status == "SHUTOFF":
                self.conn.compute.wait_for_server(self.conn.compute.find_server(server_id), new_status)
        except Exception as e:
            return False, "Failed performing server status function {0}".format(repr(e))

    def server_create(self, name, image, flavor, network=None, hypervisor=None, zone=None):
        """
        Create a Server
        :param name: Name of new server
        :param image: Name or ID
        :param flavor: Name or ID
        :param network: Name or ID
        :param hypervisor: Name or ID
        :param zone: Name of zone
        :return: (status (Bool), reason (String))
        """
        availability_zone = None
        if hypervisor and zone:
            # TODO: validate zone
            hypervisor_id = self.find_resource_id(hypervisor, self.conn.compute.find_hypervisor)
            if not hypervisor_id:
                return False, "Hypervisor not found with Name or ID {} - aborting creation".format(hypervisor)

            availability_zone = "{0}:{1}".format(
                self.conn.identity.find_hypervisor(hypervisor_id)["hypervisor_hostname"], zone)

        network_id = None
        if network:
            network_id = self.find_resource_id(network, self.conn.network.find_network)
            if not network_id:
                return False, "Network not found with Name or ID {} - aborting creation".format(network)

        image_id = self.find_resource_id(image, self.conn.compute.find_image)
        if not image_id:
            return False, "Image not found with Name or ID {} - aborting creation".format(image)

        flavor_id = self.find_resource_id(flavor, self.conn.compute.find_flavor)
        if not flavor_id:
            return False, "Flavor not found with Name or ID {} - aborting creation".format(flavor)

        try:
            self.conn.compute.create_server(name, image_id, flavor_id, network_id, availability_zone)
            return True, "Server creation successful"
        except Exception as e:
            return False, "Openstack error: {0}".format(repr(e))

    def server_delete(self, server):
        """
        Delete a Server (must be not be in ACTIVE state)
        :param server: Name or ID
        :return: (status (Bool), reason (String))
        """
        server_id = self.find_resource_id(server, self.conn.compute.find_server)
        if not server_id:
            return False, "Server not found with Name or ID {}".format(server)

        server = self.conn.compute.find_server(server_id)
        if server["status"] != "ACTIVE":
            self.conn.compute.delete_server(server)
            return True, "Server Deleted"
        else:
            return False, "Server Still ACTIVE - aborted"

    def server_restart(self, server):
        """
        Soft Restart a Server
        :param server: Name or ID
        :return: (status (Bool), reason (String))
        """
        return self.server_change_status(server, "restart")

    def server_shutdown(self, server):
        """
        Stop Server
        :param server: Name or ID
        :return: (status (Bool), reason (String))
        """
        return self.server_change_status(server, "shutdown")

    def server_reboot(self, server):
        """
        Hard Reboot Server
        :param server: Name or ID
        :return: (status (Bool), reason (String))
        """
        return self.server_change_status(server, "reboot_hard")