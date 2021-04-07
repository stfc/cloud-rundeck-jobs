from ListItems import ListItems

class ListProjects(ListItems):
    def __init__(self, conn, criteria_list, property_list):
        super().__init__(conn, lambda: conn.list_projects(),
                        self.parseCriteria(criteria_list), self.parseProperties(property_list))

    def parseCriteria(self, criteria_list):
        """ function to parse a list of criteria tuples (criteria name, args (dictionary)) """
        res = []
        for key, args in criteria_list:
            func = {
                "is_enabled": lambda dict, args=args: dict["enabled"] == True,
                "name": lambda dict, args=args: dict["name"] == args[0],
                "id": lambda dict, args=args: dict["id"] == args[0]
            }.get(key, None)
            if func:
                res.append(func)
        if not res:
            res = [lambda dict: True]
        return res

    def parseProperties(self, property_list):
        """ function to parse a list of properties """

        property_dict = {
            "project_id": lambda a :    a["id"],
            "project_name": lambda a:   a["name"],
            "project_description": lambda a: a["description"]
        }
        res = {key:property_dict.get(key, None) for key in property_list}
        return res
