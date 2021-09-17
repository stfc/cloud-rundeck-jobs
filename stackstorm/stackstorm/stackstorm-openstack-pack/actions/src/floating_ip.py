from st2common.runners.base_action import Action
import openstack
from openstack_action import OpenstackAction

class FloatingIP(OpenstackAction):
    def __init__(self, *args, **kwargs):
        """constructor class """
        super().__init__(*args, **kwargs)

        # lists possible functions that could be run as an action
        self.func = {
            "floating_ip_create": self.floating_ip_create,
            "floating_ip_delete": self.floating_ip_delete,
            "floating_ip_show": self.floating_ip_show
            # floating_ip_update
        }

    def floating_ip_show(self, ip):
        """
        Show floating ip information
        :param ip: floating ip id (String)
        :return: (status (Bool), reason/output (String/Dict))
        """
        try:
            ip = self.conn.identity.find_ip(ip, ignore_missing=False)
        except Exception as e:
            return False, "IP not found {}".format(repr(e))
        return True, ip

    def floating_ip_delete(self, ip):
        """
        Delete floating ip
        :param ip: ip id
        :return: (status (Bool), reason/output (String/Dict))
        """
        raise NotImplementedError


    def floating_ip_create(self, network, project, number_to_create):
        """
        Create floating IPs for a project
        :param network (String): ID or Name,
        :param project (String): ID or Name,
        :param number_to_create (Int): Number of floating ips to create
        :return: (status (Bool), reason (String))
        """
        #get network id
        network_id = self.find_resource_id(network, self.conn.network.find_network)
        if not network_id:
            return False, "Network not found with Name or ID {}".format(network)

        #get project id
        project_id = self.find_resource_id(project, self.conn.identity.find_project)
        if not project_id:
            return False, "Project not found with Name or ID {}".format(project)

        ip_output = []
        for i in range(number_to_create):
            try:
                ip = self.conn.network.create_ip(project_id=project_id, floating_network_id=network_id)
                ip_output.append(ip)
            except Exception as e:
                return False, "Float IP creation Failed: {0}".format(repr(e))
        return True, ip_output
