from ListItems import ListItems

class ListServers(ListItems):
    def __init__(self, conn, criteria_list, property_list):
        super().__init__(conn, lambda: conn.list_servers(all_projects=True),
                        self.parseCriteria(criteria_list), self.parseProperties(property_list))

    def parseCriteria(self, criteria_list):
        """ function to parse a list of criteria tuples (criteria name, args (dictionary)) """
        res = []
        for key, args in criteria_list:
            func = {
                "status": lambda dict, args=args: dict["status"] in args,
                "id":  lambda dict, args=args: dict["id"] in args,
                "name": lambda dict, args=args: dict["name"] in args,
                "older-than": lambda dict, args=args: isOlderThanXDays(dict, days = args),
                "hasIllegalConnections": lambda dict, args=args: hasIllegalConnections(dict),

                "user-id": lambda dict, args=args: dict["user_id"] in args,
                "user-name": lambda dict, args=args: self.conn.identity.find_user(dict["user_id"])["name"] in args,

                "host-id": lambda dict, args=args: dict["host_id"] in args,
                "host-name": lambda dict, args=args: dict["hypervisor_hostname"] in args
            }.get(key, None)
            if func:
                res.append(func)
        if not res:
            res = [lambda dict: True]
        return res

    def parseProperties(self, property_list):
        """ function to parse a list of properties """

        property_dict = {
            "user_id":lambda a :    a["user_id"],
            "user_name":lambda a :  self.conn.identity.find_user(a["user_id"])["name"],
            "user_email":lambda a : self.conn.identity.find_user(a["user_id"])["email"],

            "host_id": lambda a :   a["host_id"],
            "host_name":lambda a :  a["hypervisor_hostname"],

            "server_id": lambda a : a["id"],
            "server_name": lambda a :   a["name"],
            "server_status": lambda a : a["status"],
            "server_creation_date": lambda a : a["created_at"],

            "project_id": lambda a :    a["location"]["project"]["id"],
            "project_name": lambda a:   a["location"]["project"]["name"]
        }
        res = {key:property_dict.get(key, None) for key in property_list}
        return res
