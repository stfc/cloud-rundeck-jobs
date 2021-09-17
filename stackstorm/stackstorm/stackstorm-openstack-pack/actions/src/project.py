from st2common.runners.base_action import Action
import openstack
from openstack_action import OpenstackAction

class Project(OpenstackAction):
    def __init__(self, *args, **kwargs):
        """ constructor class """
        super().__init__(*args, **kwargs)

        # lists possible functions that could be run as an action
        self.func = {
            "project_show": self.project_show,
            "project_create": self.project_create,
            "project_delete": self.project_delete
            # project_update
        }

    def project_delete(self, project):
        """
        Delete a project
        :param project: project Name or ID
        :return: (status (Bool), reason (String))
        """
        raise NotImplementedError

    def project_show(self, project, domain):
        """
        find and return a given project's properties
        :param project:(String) Name or ID,
        :param domain:(String) Domain Name or ID
        :return: (status (Bool), reason (String))
        """

        domain_id = self.find_resource_id(domain, self.conn.identity.find_domain)
        if not domain_id:
            return False, "No domain found with Name or ID {}".format(domain)
        try:
            project = self.conn.identity.find_project(project, domain_id=domain_id)
        except Exception as e:
            return False, "Finding Project Failed {}".format(e)
        return True, project

    def project_create(self, domain, name, description, is_enabled):
        """
        find and return a given project's properties
        :param domain: (String) Name or ID,
        :param name: (String) Name of new project
        :param description: (String) Description for new project
        :param is_enabled: (Bool) Set if new project enabled or disabled
        :return: (status (Bool), reason (String))
        """

        domain_id = self.find_resource_id(domain, self.conn.identity.find_domain)
        if not domain_id:
            return False, "No domain found with Name or ID {}".format(domain)
        try:
            project = self.conn.identity.create_project(domain_id=domain_id,
                                                        name=name,
                                                        description=description,
                                                        is_enabled=is_enabled)
        except Exception as e:
            return False, "Project Creation Failed {}".format(e)
        return True, project
