from ListItems import ListItems

class ListHosts(ListItems):
    def __init__(self, conn, criteria_list, property_list):
        super().__init__(conn, lambda: conn.list_hypervisors(),
                        self.parseCriteria(criteria_list), self.parseProperties(property_list))

    def parseCriteria(self, criteria_list):
        """ function to parse a list of criteria tuples (criteria name, args (dictionary)) """
        res = []
        for key, args in criteria_list:
            func = {
                "status": lambda dict, args=args: dict["status"] in args[0],
                "name": lambda dict, args=args: dict["name"] in args[0],
                "id": lambda dict, args=args: dict["id"] in args[0],

                "project-id": lambda dict, args=args: dict["location"]["project"]["id"] in args,
                "project-name": lambda dict, args=args: dict["location"]["project"]["name"] in args
            }.get(key, None)
            if func:
                res.append(func)
        if not res:
            res = [lambda dict: True]
        return res

    def parseProperties(self, property_list):
        """ function to parse a list of properties """

        property_dict = {
            "host_id": lambda a :   a["host_id"],
            "host_name":lambda a :  a["hypervisor_hostname"],

            "project_id": lambda a :    a["location"]["project"]["id"],
            "project_name": lambda a:   a["location"]["project"]["name"]
        }
        res = {key:property_dict.get(key, None) for key in property_list}
        return res
