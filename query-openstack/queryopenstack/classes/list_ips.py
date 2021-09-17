from .list_items import ListItems

class ListIps(ListItems):
    """
    A class to list float ips: Inherits from ListItems

    Attributes
    ----------
    criteria_func_dict: dict
        stores possible query criteria options -
        criteria name (key) : function to evaluate a criteria on ip (value)
                function (bool) - evaluate 'ip' properties against criteria
                overrides ListItems attribute

    property_func_dict: dict
        stores possible ip property options
        property name (key) : function to retrieve property (value)
                function (string/int) - returns property value from a 'ip' dictionary
    """
    def __init__(self, conn):
        '''constructor class'''
        super().__init__(conn, lambda: conn.list_floating_ips())

        self.criteria_func_dict = {
            "status": lambda dict, args: dict["status"] in args,
            "not_status": lambda dict, args: dict["status"] not in args,

            "attached": lambda dict, args: dict["attached"] == True,
            "not_attached": lambda dict, args: dict["attached"] == False,

            "id": lambda dict, args: dict["id"] in args,
            "not_id": lambda dict, args: dict["id"] not in args,

            "project_id": lambda dict, args: dict["project_id"] in args,
            "not_project_id": lambda dict, args: dict["project_id"] not in args,

            "older_than": lambda dict, args: self.isOlderThanXDays(dict, days = args),
            "not_older_than": lambda dict, args: not self.isOlderThanXDays(dict, days = args),

            "project_name": lambda dict, args: self.conn.identity.find_project(dict["project_id"])["name"] in args,
            "not project_name": lambda dict, args: self.conn.identity.find_project(dict["project_id"])["name"] not in args,
            "project_name_contains": lambda dict, args: any(arg in self.conn.identity.find_project(dict["project_id"])["name"] for arg in args),
            "project_name_not_contains": lambda dict, args: any(arg not in self.conn.identity.find_project(dict["project_id"])["name"] for arg in args)
        }

        self.property_func_dict = {
            "ip_id": lambda a :    a["id"],
            "ip_fixed_address": lambda a:   a["fixed_ip_address"],
            "ip_floating_address": lambda a:  a["floating_ip_address"],
            "ip_port_id": lambda a: a["port_id"],
            "ip_created_at": lambda:  a["created_at"],

            "project_id": lambda a :    a["project_id"],
            "project_name": lambda a:   self.conn.identity.find_project(a["project_id"])["name"]
        }
