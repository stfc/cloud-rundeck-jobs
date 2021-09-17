from st2common.runners.base_action import Action
import openstack

class OpenstackAction(Action):
    def run(self, **kwargs):
        """
        function that is run by stackstorm when an action is invoked
        :param kwargs: arguments for openstack actions
        :return: (Status (Bool), Output <*>): tuple of action status (succeeded(T)/failed(F)) and the output
        """
        self.conn = self.connect_to_openstack()
        fn = self.func.get(kwargs["submodule"])
        return fn(**{k:v for k, v in kwargs.items() if v not in [None, ["NULL"]] and k not in ["submodule"]})


    def find_resource_id(self, identifier, openstack_func, **kwargs):
        """
        helper to find the ID of a openstack resource
        :param identifier: Associated Name of the openstack resource
        :param openstack_func: Openstack function to find the resource
        :param kwargs: Arguments to pass into Openstack function
        :return: (String/None): ID of resource (or None if not found)
        """
        resource = openstack_func(identifier, **kwargs)
        if not resource:
            return None
        return resource.get("id", None)

    def connect_to_openstack(self):
        """
        Connect to openstack
        :return: openstack connection object
        """
        return openstack.connect()
