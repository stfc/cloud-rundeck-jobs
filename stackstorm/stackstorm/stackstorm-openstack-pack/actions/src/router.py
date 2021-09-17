from st2common.runners.base_action import Action
import openstack
import random
from openstack_action import OpenstackAction

class Router(OpenstackAction):

    def __init__(self, *args, **kwargs):
        """ constructor class """
        super().__init__(*args, **kwargs)

        # lists possible functions that could be run as an action
        self.func = {
            "router_create": self.router_create,
            "router_add_interface": self.router_add_interface,
            "router_remove_interface": self.router_remove_interface,
            "router_delete": self.router_delete,
            "router_show": self.router_show,
            "router_update": self.router_update
        }

    def router_create(self, project, external_gateway, **router_kwargs):
        """
        Create openstack router for project
        :param project: (String) Name or ID
        :param external_gateway: (String) Name or ID,
        :param router_kwargs - see action definintion yaml file for details)
        :return: (status (Bool), reason (String))
        """

        project_id = self.find_resource_id(project, self.conn.identity.find_project)
        if not project_id:
            return False, "Project not found with Name or ID {}".format(project)

        external_gateway_id = self.find_resource_id(external_gateway, self.conn.network.find_network)
        if not external_gateway_id:
            return False, "Network (External Gateway) not found with Name or ID {}".format(external_gateway)
        try:
            router = self.conn.network.create_router(project_id=project_id, external_gateway_info={"network_id":external_gateway_id}, **router_kwargs)
        except Exception as e:
            return False, "Router Creation Failed {}".format(e)
        return True, router

    def router_add_interface(self, router, subnet, port):
        """
        Add interface to Openstack router
        :param router: (String) ID or Name
        :param subnet: (String) ID or Name,
        :param port: (String) ID or Name
        :return: (status (Bool), reason (String))
        """

        # requires either subnet_id or port_id
        subnet_id, port_id = None, None

        # get router id
        router_id = self.find_resource_id(router, self.conn.network.find_router)
        if not router_id:
            return False, "Router not found with Name or ID {}".format(router)

        # if subnet provided - get subnet id
        if subnet:
            subnet_id = self.find_resource_id(subnet, self.conn.network.find_subnet)
            if not router_id:
                return False, "Router not found with Name or ID {}".format(subnet)

        # if port provided - get port id
        if port:
            port_id = self.find_resource_id(port, self.conn.network.find_port)
            if not port_id:
                return False, "Port not found with Name or ID {}".format(port)

        try:
            router = self.conn.network.add_interface_to_router(router=router_id, subnet_id=subnet_id, port_id=port_id)
        except Exception as e:
            return False, "Adding Router Interface Failed {}".format(e)
        return True, router

    def router_remove_interface(self, router, subnet, port):
        """
        Remove interface to Openstack router
        :param router: (String) ID or Name
        :param subnet: (String) ID or Name,
        :param port: (String) ID or Name
        :return: (status (Bool), reason (String))
        """

        # requires either subnet_id or port_id
        subnet_id, port_id = None, None

        # get router id
        router_id = self.find_resource_id(router, self.conn.network.find_router)
        if not router_id:
            return False, "Router not found with Name or ID {}".format(router)

        # if subnet provided - get subnet id
        if subnet:
            subnet_id = self.find_resource_id(subnet, self.conn.network.find_subnet)
            if not router_id:
                return False, "Router not found with Name or ID {}".format(subnet)

        # if port provided - get port id
        if port:
            port_id = self.find_resource_id(port, self.conn.network.find_port)
            if not port_id:
                return False, "Port not found with Name or ID {}".format(port)

        try:
            router = self.conn.network.remove_interface_from_router(router=router_id, subnet_id=subnet_id, port_id=port_id)
        except Exception as e:
            return False, "Removing Router Interface Failed {}".format(e)
        return True, router

    def router_show(self, router):
        """
        Show router properties
        :param router: Name or ID
        :return: (status (Bool), reason (String))
        """
        try:
            router = self.conn.network.find_router(router, ignore_missing=False)
        except Exception as e:
            return False, "Router not found {}".format(repr(e))
        return True, router

    def router_delete(self, router):
        """
        Delete router
        :param router: Name or ID
        :return: (status (Bool), reason (String))
        """
        raise NotImplementedError

    def router_update(self, router, **update_kwargs):
        """
        Update router properties
        :param router: Name or ID
        :param update_kwargs: see action definintion yaml file for details)
        :return: (status (Bool), reason (String))
        """
        raise NotImplementedError