from openstack_action import OpenstackAction
from queryopenstack.query import Query
from tabulate import tabulate


class SearchOpenstack(OpenstackAction):
    def __init__(self, *args, **kwargs):
        """ constructor class """
        super().__init__(*args, **kwargs)

        # different methods of searching openstack
        self.func = {
            "search_openstack": lambda search_by, query_preset, get_html, search_criteria=None, properties_to_select=None, sort_by_criteria=None, **kwargs:
            self.output_results(
                query_result=self.get_preset(
                    search_by=search_by,
                    query_preset=query_preset,
                    criteria_list=search_criteria,
                    properties_list=properties_to_select,
                    sort_by_list=sort_by_criteria,
                    **kwargs
                ),
                get_html=get_html,
            ),

            "search_servers_per_user": lambda query_preset, get_html, search_criteria=None, properties_to_select=None, sort_by_criteria=None, **kwargs:
            self.search_servers_per_user(
                query_result=self.get_preset(
                    search_by="server",
                    query_preset=query_preset,
                    criteria_list=search_criteria,
                    properties_list=properties_to_select,
                    sort_by_list=sort_by_criteria,
                    **kwargs
                ),
                get_html=get_html,
            ),
        }

    @staticmethod
    def get_preset(search_by, query_preset, criteria_list, properties_list, sort_by_list, **kwargs):
        """
        A number of predefined presets for searching openstack
        :param search_by: openstack objects to search for
        :param query_preset: preset name to use
        :param criteria_list: list of extra criteria
        :param properties_list: list of properties to find for openstack object
        :param sort_by_list: field to sort results by
        :param kwargs: other properties
        :return: dict/None - query results
        """

        # if no preset selected - use generic query method
        if query_preset == "no_preset":
            return Query(by=search_by,
                         properties_list=properties_list,
                         criteria_list=criteria_list,
                         sort_by_list=sort_by_list,
                         output_to_console=False,
                         save=False,
                         save_path="")

        # search by ID presets (works for all openstack objects)
        func = {
            "id_in": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                Query(by=search_by,
                      properties_list=properties_list,
                      criteria_list=[["id", [name for name in kwargs["ids"]]]].extend(criteria_list)
                        if criteria_list else [["id", [name for name in kwargs["ids"]]]],
                      sort_by_list=sort_by_list,
                      output_to_console=False,
                      save=False,
                      save_path=""),

            "id_not_in": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                Query(by=search_by,
                      properties_list=properties_list,
                      criteria_list=[["not_id", [name for name in kwargs["ids"]]]].extend(criteria_list)
                        if criteria_list else [["not_id", [name for name in kwargs["ids"]]]],
                      sort_by_list=sort_by_list,
                      output_to_console=False,
                      save=False,
                      save_path="")
        }.get(query_preset, None)

        # search by Name presets (works for all openstack objects with associated names)
        if not func and search_by != "ip":
            func = {
                "name_in": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                    Query(by=search_by,
                          properties_list=properties_list,
                          criteria_list=[["name"] + [name if name[:7] != "http://" else name[7:] for name in kwargs["names"]]].extend(criteria_list)
                            if criteria_list else [["name"] + [name if name[:7] != "http://" else name[7:] for name in kwargs["names"]]],
                          sort_by_list=sort_by_list,
                          output_to_console=False,
                          save=False,
                          save_path=""),

                "name_not_in": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                    Query(by=search_by,
                          properties_list=properties_list,
                          criteria_list=[["not_name"] + [name if name[:7] != "http://" else name[7:] for name in kwargs["names"]]].extend(criteria_list)
                            if criteria_list else [["not_name"] + [name if name[:7] != "http://" else name[7:] for name in kwargs["names"]]],
                          sort_by_list=sort_by_list,
                          output_to_console=False,
                          save=False,
                          save_path=""),

                "name_contains": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                    Query(by=search_by,
                          properties_list=properties_list,
                          criteria_list=[["name_contains", name] for name in kwargs["name_snippets"]].extend(criteria_list)
                            if criteria_list else [["name_contains", name] for name in kwargs["name_snippets"]],
                          sort_by_list=sort_by_list,
                          output_to_console=False,
                          save=False,
                          save_path=""),

                "name_not_contains": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                    Query(by=search_by,
                          properties_list=properties_list,
                          criteria_list=[["name_not_contains", name] for name in kwargs["name_snippets"]].extend(criteria_list)
                            if criteria_list else [["name_not_contains", name] for name in kwargs["name_snippets"]],
                          sort_by_list=sort_by_list,
                          output_to_console=False,
                          save=False,
                          save_path="")
            }.get(query_preset, None)

        # more specific presets which are unique to specific openstack object
        if not func:
            func = {
                "server": {
                    "server_error_and_shutoff": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                        Query(by="server",
                              properties_list=properties_list,
                              criteria_list=[["status", "SHUTOFF", "ERROR"]].extend(criteria_list)
                                if criteria_list else [["status", "SHUTOFF", "ERROR"]],
                              sort_by_list=sort_by_list,
                              output_to_console=False,
                              save=False,
                              save_path=""),

                    "server_shutoff": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                        Query(by="server",
                              properties_list=properties_list,
                              criteria_list=[["status", "SHUTOFF"]].extend(criteria_list)
                                if criteria_list else [["status", "SHUTOFF"]],
                              sort_by_list=sort_by_list,
                              output_to_console=False,
                              save=False,
                              save_path=""),

                    "server_error": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                        Query(by="server",
                              properties_list=properties_list,
                              criteria_list=[["status", "ERROR"]].extend(criteria_list)
                                if criteria_list else [["status", "ERROR"]],
                              sort_by_list=sort_by_list,
                              output_to_console=False,
                              save=False,
                              save_path=""),

                    "server_older_than": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                        Query(by="server",
                              properties_list=properties_list,
                              criteria_list=[["older_than", kwargs["days"]]].extend(criteria_list)
                                if criteria_list else [["older_than", kwargs["days"]]],
                              sort_by_list=sort_by_list,
                              output_to_console=False,
                              save=False,
                              save_path=""),

                    "server_younger_than": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                        Query(by="server",
                              properties_list=properties_list,
                              criteria_list=[["not_older_than", kwargs["days"]]].extend(criteria_list)
                                if criteria_list else [["not_older_than", kwargs["days"]]],
                              sort_by_list=sort_by_list,
                              output_to_console=False,
                              save=False,
                              save_path="")
                },
                "ip": {
                    "in_projects": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                        Query(by="ip",
                              properties_list=properties_list,
                              criteria_list=[["project_id"] + [name for name in kwargs["project_ids"]]].extend(criteria_list)
                                if criteria_list else [["project_id"] + [name for name in kwargs["project_ids"]]],
                              sort_by_list=sort_by_list,
                              output_to_console=False,
                              save=False,
                              save_path="")
                },
                "host": {
                    "host_enabled": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                        Query(by="host",
                              properties_list=properties_list,
                              criteria_list=[["status", "enabled"]].extend(criteria_list)
                                if criteria_list else [["status", "enabled"]],
                              sort_by_list=sort_by_list,
                              output_to_console=False,
                              save=False,
                              save_path=""),

                    "host_disabled": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                        Query(by="host",
                              properties_list=properties_list,
                              criteria_list=[["status", "disabled"]].extend(criteria_list)
                                if criteria_list else [["status", "disabled"]],
                              sort_by_list=sort_by_list,
                              output_to_console=False,
                              save=False,
                              save_path="")
                },
                "project": {
                    "description_contains": lambda properties_list, criteria_list, sort_by_list, **kwargs:
                        Query(by="project",
                              properties_list=properties_list,
                              criteria_list=[["description_contains", description] for description in kwargs["description_snippets"]].extend(criteria_list)
                                if criteria_list else [["description_contains", description] for description in kwargs["description_snippets"]],
                              sort_by_list=sort_by_list,
                              output_to_console=False,
                              save=False,
                              save_path="")
                }
            }.get(search_by, {}).get(query_preset, None)

        # run the query and return the results
        return func(properties_list, criteria_list, sort_by_list, **kwargs) if func else None

    @staticmethod
    def output_results(query_result, get_html=False):
        """
        Output the resulting query results
        :param query_result: dict of query results
        :param get_html: True if output required in html table format else output plain text table
        :return: Status (Bool), String (html or plaintext table of results)
        """
        if not query_result:
            return False, "No data found"
        headers = query_result[0].keys()
        rows = [row.values() for row in query_result]
        return True, tabulate(rows, headers, tablefmt="html" if get_html else "grid")

    def search_servers_per_user(self, query_result, get_html=False):
        if not query_result:
            return False, "No data found"
        user_server_dict = {}
        for server in query_result:
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
            _, user_server_dict[email] = self.get_output(servers, get_html)

        return True, user_server_dict
