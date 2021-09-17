from st2common.runners.base_action import Action
import openstack
import random
import re
from openstack_action import OpenstackAction


class Subnet(OpenstackAction):

    def __init__(self, *args, **kwargs):
        """ constructor class """
        super().__init__(*args, **kwargs)

        # lists possible functions that could be run as an action
        self.func = {
            "subnet_create": self.subnet_create,
            "subnet_update": self.subnet_update,
            "subnet_delete": self.subnet_delete,
            "subnet_show": self.subnet_show
        }

    def subnet_delete(self, subnet):
        """
        Delete a subnet
        :param subnet: Name or ID
        :return: (status (Bool), reason/output (String/Dict))
        """
        raise NotImplementedError

    def subnet_update(self, subnet, **update_kwargs):
        """
        Update a subnet
        :param subnet: Name or ID
        :param update_kwargs: update properties
        :return: (status (Bool), reason/output (String/Dict))
        """
        raise NotImplementedError

    def subnet_show(self, subnet):
        """
        Show subnet properties
        :param subnet: Name or ID
        :return: (status (Bool), reason/output (String/Dict))
        """
        try:
            subnet = self.conn.network.find_subnet(subnet, ignore_missing=False)
        except Exception as e:
            return False, "Subnet not found {}".format(repr(e))
        return True, subnet

    def subnet_create(self, network, **subnet_kwargs):
        """
        Create a Subnet on a Network
        :param network: (String) ID or Name
        :param subnet_kwargs: (other_args - see action definintion yaml file for details)
        :return: (status (Bool), reason/output (String/Dict))
        """

        # calculate and choose random available gateway ip
        currently_used = [subnet["gateway_ip"].split(".")[2] for subnet in self.conn.network.subnets() if re.search("^192.168.", str(subnet["gateway_ip"]))]
        available_byte3 = list(set([str(x) for x in range(1, 255)]) - set(currently_used))

        byte3 = random.choice(available_byte3)
        cidr = "192.168.{}.0/24".format(byte3)
        subnet_start = "192.168.{}.10".format(byte3)
        subnet_end = "192.168.{}.254".format(byte3)
        gateway_ip = "192.168.{}.1".format(byte3)

        # get network id
        network_id = self.find_resource_id(network, self.conn.network.find_network)
        if not network_id:
            return False, "No Network Found with Name or ID {}".format(network)

        try:
            subnet = self.conn.network.create_subnet(ip_version=4,
                                                     network_id=network_id,
                                                     allocation_pools=[{"start": subnet_start, "end": subnet_end}],
                                                     cidr=cidr,
                                                     gateway_ip=gateway_ip,
                                                     **subnet_kwargs)
        except Exception as e:
            return False, "Subnet Creation Failed {}".format(e)
        return True, subnet
