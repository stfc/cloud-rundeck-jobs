from st2common.runners.base_action import Action
from openstack_action import OpenstackAction
from queryopenstack.query import Query
from tabulate import tabulate
import csv
"""
TODO: DEPRECATED - REMOVE AND ADD:
    
    server update - update properties
    server create - create server
    server delete - delete server
    server show - show server
    server debug - show debug info
    
    server evacuate - evacuate server 
    server migrate - migrate server 
    
    server set status - change server status
    
    server group create - create server group
    server group update - update server group
    server group delete - delete server group
    server group show - show server group
    
"""
class Server(OpenstackAction):
    def __init__(self, *args, **kwargs):
        """ constructor class """
        super().__init__(*args, **kwargs)

        # lists possible functions that could be run as an action
        self.func = {
            "server_list_shutoff": lambda **kwargs: self.get_output(
                result_list=self.get_servers(
                    base_criteria=[["status", "SHUTOFF"]],
                    criteria_list = kwargs["search_criteria"] if "search_criteria" in kwargs.keys() else None,
                    properties_to_select=kwargs["properties_to_select"],
                    sort_by_criteria=kwargs["sort_by_criteria"] if "sort_by_criteria" in kwargs.keys() else None,
                ),
                get_html=kwargs["get_html"],
            ),

            "server_shutoff_per_user": lambda **kwargs: self.get_output_per_user(
                result_list=self.get_servers(
                    base_criteria=[["status", "SHUTOFF"]],
                    criteria_list = kwargs["search_criteria"] if "search_criteria" in kwargs.keys() else None,
                    properties_to_select=kwargs["properties_to_select"],
                    sort_by_criteria=kwargs["sort_by_criteria"] if "sort_by_criteria" in kwargs.keys() else None,
                ),
                get_html=kwargs["get_html"],
            ),

            "server_list_error": lambda **kwargs: self.get_output(
                result_list=self.get_servers(
                    base_criteria=[["status", "ERROR"]],
                    criteria_list = kwargs["search_criteria"] if "search_criteria" in kwargs.keys() else None,
                    properties_to_select=kwargs["properties_to_select"],
                    sort_by_criteria=kwargs["sort_by_criteria"] if "sort_by_criteria" in kwargs.keys() else None,
                ),
                get_html=kwargs["get_html"],
            ),

            "server_error_per_user": lambda **kwargs: self.get_output_per_user(
                result_list=self.get_servers(
                    base_criteria=[["status", "ERROR"]],
                    criteria_list = kwargs["search_criteria"] if "search_criteria" in kwargs.keys() else None,
                    properties_to_select=kwargs["properties_to_select"],
                    sort_by_criteria=kwargs["sort_by_criteria"] if "sort_by_criteria" in kwargs.keys() else None,
                ),
                get_html=kwargs["get_html"],
            ),

            "server_list_older_than": lambda **kwargs: self.get_output(
                result_list=self.get_servers(
                    base_criteria=[["older_than", kwargs["days"]]],
                    criteria_list=kwargs["search_criteria"] if "search_criteria" in kwargs.keys() else None,
                    properties_to_select=kwargs["properties_to_select"],
                    sort_by_criteria=kwargs["sort_by_criteria"] if "sort_by_criteria" in kwargs.keys() else None,
                ),
                get_html=kwargs["get_html"],
            ),

            "server_list_older_than_per_user": lambda **kwargs: self.get_output_per_user(
                result_list=self.get_servers(
                    base_criteria=[["older_than", kwargs["days"]]],
                    criteria_list=kwargs["search_criteria"] if "search_criteria" in kwargs.keys() else None,
                    properties_to_select=kwargs["properties_to_select"],
                    sort_by_criteria=kwargs["sort_by_criteria"] if "sort_by_criteria" in kwargs.keys() else None,
                ),
                get_html=kwargs["get_html"],
            ),

            "server_list_younger_than": lambda **kwargs: self.get_output(
                result_list=self.get_servers(
                    base_criteria=[["not_older_than", kwargs["days"]]],
                    criteria_list=kwargs["search_criteria"] if "search_criteria" in kwargs.keys() else None,
                    properties_to_select=kwargs["properties_to_select"],
                    sort_by_criteria=kwargs["sort_by_criteria"] if "sort_by_criteria" in kwargs.keys() else None,
                ),
                get_html=kwargs["get_html"],
            ),

            "server_list_younger_than_per_user": lambda **kwargs: self.get_output_per_user(
                result_list=self.get_servers(
                    base_criteria=[["not_older_than", kwargs["days"]]],
                    criteria_list=kwargs["search_criteria"] if "search_criteria" in kwargs.keys() else None,
                    properties_to_select=kwargs["properties_to_select"],
                    sort_by_criteria=kwargs["sort_by_criteria"] if "sort_by_criteria" in kwargs.keys() else None,
                ),
                get_html=kwargs["get_html"],
            ),
        }

    def get_servers(self, base_criteria, criteria_list, properties_to_select=None, sort_by_criteria=None):
        """
        Get Server info based on certain search criteria
        :param base_criteria: list: [["criteria_name_1", "arg1", "arg2", etc], ["criteria_name_2"], etc]
        criteria to search servers by
        :param criteria_list: list: Extra criteria, same format as base_criteria (can be None)
        :param properties_to_select: list ["property_1", "property_2", etc]: properties to select for each server
        :param sort_by_criteria: list ["property_1", etc]: properties to sort the final results by
        :return: [{property_1: "value", property_2: "value"}, etc]: dictionary with results of server query
        """
        criteria = base_criteria.extend(criteria_list) if criteria_list else base_criteria
        return Query(
            by="server",
            properties_list=properties_to_select,
            criteria_list=criteria,
            sort_by_list=sort_by_criteria,
            output_to_console=False,
            save=False,
            save_path=""
        )

    def get_output(self, result_list, get_html):
        """
        Get Server Query as Html or String Output
        :param result_list: dictionary with results of a server query
        :param get_html: boolean to return html format or plaintext
        :return: (status (Bool), reason/output (String))

        """
        if result_list:
            headers = result_list[0].keys()
            rows = [row.values() for row in result_list]
            return True, tabulate(rows, headers, tablefmt="html" if get_html else "grid")
        return True, "None found"

    def get_output_per_user(self, result_list, get_html):
        """
        Get Server Query per user as HTML or String Output
        :param result_list: dictionary with results of a server query
        :param get_html: boolean to return html format or plaintext
        :return: (status (Bool), output (Dict))
        """
        user_server_dict = {}
        if result_list:
            for server in result_list:
                user_email = server["user_email"]
                if user_email in user_server_dict.keys():
                    user_server_dict[user_email].append(server)
                else:
                    user_server_dict[user_email] = [server]

            if "not found" in user_server_dict.keys():
                print("Following Servers found with no associated Email")
                print(self.get_output(user_server_dict["not found"], False))
                del user_server_dict["not found"]

            for email in user_server_dict.keys():
                servers = user_server_dict[email]
                user_server_dict[email] = self.get_output(servers, get_html)

        return True, user_server_dict



