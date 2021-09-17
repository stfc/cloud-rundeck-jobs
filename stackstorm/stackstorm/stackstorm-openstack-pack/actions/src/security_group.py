from st2common.runners.base_action import Action
import openstack
from subprocess import Popen, PIPE
from openstack_action import OpenstackAction
import os
SOURCECMD = "source /etc/openstack/openrc/admin-openrc.sh;"


class SecurityGroup(OpenstackAction):
    def __init__(self, *args, **kwargs):
        """ constructor class """
        super().__init__(*args, **kwargs)

        # lists possible functions that could be run as an action
        self.func = {
            "security_group_create": self.security_group_create,
            "security_group_rule_create": self.security_group_rule_create,
            "security_group_show": self.security_group_show,
            "security_group_list": self.security_group_list
            # security_group_delete
            # security_group_update
        }

    def security_group_create(self, project, **security_group_kwargs):
        """
        Create a Security Group for a Project
        :param project: (String) ID or Name,
        :param security_group_kwargs - see action definintion yaml file for details
        :return: (status (Bool), reason (String))
        """
        # get project id
        project_id = self.find_resource_id(project, self.conn.identity.find_project)
        if not project_id:
            return False, "Project not found with Name or ID {}".format(project)

        try:
            security_group = self.conn.network.create_security_group(project_id=project_id, **security_group_kwargs)
        except Exception as e:
            return False, "Security Group Creation Failed {}".format(e)
        return True, security_group

    def security_group_show(self, project, security_group):
        """
        Show a security group
        :param project: ID or Name,
        :param security_group: ID or Name
        :return: (status (Bool), reason (String))
        """

        # if project specified - show security group info for that project
        if project:
            project_id = self.find_resource_id(project, self.conn.identity.find_project)
            if not project_id:
                return False, "Project not found with Name or ID {}".format(project)

            try:
                security_group = self.conn.network.find_security_group(security_group, project_id=project_id)
            except Exception as e:
                return False, "Finding Project Failed {}".format(e)
        else:
            try:
                security_group = self.conn.network.find_security_group(security_group)
            except Exception as e:
                return False, "Finding Project Failed {}".format(e)
        return True, security_group

    def security_group_list(self, project):
        """
        List Security groups for a project
        :param project:(String) Name or ID
        :return: (status (Bool), reason (String))
        """
        project_id = self.find_resource_id(project, self.conn.identity.find_project)
        if not project_id:
            return False, "Project not found with Name or ID {}".format(project)

        # needs to be called when creating new project, openstacksdk fails to find security groups unless this is called
        p = Popen(SOURCECMD+"openstack security group list --project {} -f json".format(project_id),
                  shell=True, stdout=PIPE, env=os.environ.copy())
        _ = p.communicate()[0]

        try:
            security_groups = self.conn.network.security_groups(project_id=project_id)
            all_groups = []
            for group in security_groups:
                all_groups.append(group)
        except Exception as e:
            return False, "Listing Security Groups Failed {}".format(e)
        return True, all_groups

    def security_group_rule_create(self, security_group, project, dst_port, **security_group_kwargs):
        """
        Creature security group rule
        :param security_group: (String) Name or ID
        :param project: (String) Name or ID,
        :param dst_port: (String: <Int>:<Int>) Min and Max port range,
        :param security_group_kwargs: other_args - see action definintion yaml file for details
        :return: (status (Bool), reason (String))
        """

        # get project id
        project_id = self.find_resource_id(project, self.conn.identity.find_project)
        if not project_id:
            return False, "Project not found with Name or ID {}".format(project)

        # get security group id
        security_group_id = self.find_resource_id(security_group, self.conn.network.find_security_group,
                                                  project_id=project_id)
        if not security_group_id:
            return False, "Security group not found with Name or ID {0} for Project {1}".format(security_group, project)

        # get min and max port ranges
        if dst_port:
            port_range_min, port_range_max = dst_port.split(":")
        else:
            port_range_min, port_range_max = None, None

        try:
            security_group_rule = self.conn.network.create_security_group_rule(
                project_id=project_id,
                security_group_id=security_group_id,
                port_range_max=port_range_max,
                port_range_min=port_range_min,
                **security_group_kwargs
            )
        except openstack.exceptions.ConflictException:
            return True, "Security Group Rule direction={0}, ether_type={1}, protocol={2}, " \
                         "remote_ip_prefix={3}, dst_port={4} exist for project {5}".format(
                security_group_kwargs["direction"],
                security_group_kwargs["ether_type"],
                security_group_kwargs["protocol"],
                security_group_kwargs["remote_ip_prefix"],
                str(port_range_max)+":"+str(port_range_min),
                project_id
            )
        except Exception as e:
            return False, "Security group rule creation failed {}".format(e)
        return True, security_group_rule
