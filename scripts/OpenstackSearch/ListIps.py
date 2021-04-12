from ListItems import ListItems

class ListIps(ListItems):
    criteria_func_dict = {
        "status": lambda dict, args: dict["status"] in args,
        "not_status": lambda dict, args: dict["status"] not in args,

        "attached": lambda dict, args: dict["attached"] == True,
        "not_attached": lambda dict, args: dict["attached"] == False,

        "id": lambda dict, args: dict["id"] in args,
        "not_id": lambda dict, args: dict["id"] not in args,

        "project_id": lambda dict, args: dict["project_id"] in args,
        "not_project_id": lambda dict, args: dict["project_id"] not in args,

        "project_name": lambda dict, args: self.conn.identity.find_project(dict["project_id"])["name"] in args,
        "not project_name": lambda dict, args: self.conn.identity.find_project(dict["project_id"])["name"] not in args,
        "project_name_contains": lambda dict, args: any(arg in self.conn.identity.find_project(dict["project_id"])["name"] for arg in args),
        "project_name_not_contains": lambda dict, args: any(arg not in self.conn.identity.find_project(dict["project_id"])["name"] for arg in args)
    }

    property_func_dict = {
        "ip_id": lambda a :    a["id"],
        "ip_fixed_address": lambda a:   a["fixed_ip_address"],
        "ip_floating_address": lambda a:  a["floating_ip_address"],
        "ip_port_id": lambda a: a["port_id"],

        "project_id": lambda a :    a["project_id"],
        "project_name": lambda a:   self.conn.identity.find_project(a["project_id"])["name"]
    }

    def __init__(self, conn, criteria_list, property_list):
        super().__init__(conn, lambda: conn.list_floating_ips(),
                        criteria_list, property_list)
