from ListItems import ListItems

class ListIps(ListItems):
    def __init__(self, conn, criteria_list, property_list):
        super().__init__(conn, lambda: conn.list_floating_ips(),
                        self.parseCriteria(criteria_list), self.parseProperties(property_list))

    def parseCriteria(self, criteria_list):
        """ function to parse a list of criteria tuples (criteria name, args (dictionary)) """
        res = []
        for key, args in criteria_list:
            func = {
                "status": lambda dict, args=args: dict["status"] in args,
                "attached": lambda dict, args=args: dict["attached"] == True,
                "id": lambda dict, args=args: dict["id"] in args,

                "project-id": lambda dict, args=args: dict["project_id"] in args,
                "project-name": lambda dict, args=args: self.conn.identity.find_project(dict["project_id"])["name"] in args
            }.get(key, None)
            if func:
                res.append(func)
        if not res:
            res = [lambda dict: True]
        return res

    def parseProperties(self, property_list):
        """ function to parse a list of properties """

        property_dict = {
            "ip_id": lambda a :    a["id"],
            "ip_fixed_address": lambda a:   a["fixed_ip_address"],
            "ip_floating_address": lambda a:  a["floating_ip_address"],
            "ip_port_id": lambda a: a["port_id"],

            "project_id": lambda a :    a["project_id"],
            "project_name": lambda a:   self.conn.identity.find_project(a["project_id"])["name"]
        }
        res = {key:property_dict.get(key, None) for key in property_list}
        return res
