from ListItems import ListItems

class ListUsers(ListItems):
    def __init__(self, conn, criteria_list, property_list):
        super().__init__(conn, lambda: conn.list_users(),
                        self.parseCriteria(criteria_list), self.parseProperties(property_list))

    def parseCriteria(self, criteria_list):
        """ function to parse a list of criteria tuples (criteria name, args (dictionary)) """
        res = []
        for key, args in criteria_list:
            func = {
                "is_enabled": lambda dict, args=args: dict["enabled"] == True,
                "name": lambda dict, args=args: dict["name"] in args,
                "id": lambda dict, args=args: dict["id"] in args
            }.get(key, None)
            if func:
                res.append(func)
        if not res:
            res = [lambda dict: True]
        return res

    def parseProperties(self, property_list):
        """ function to parse a list of properties """

        property_dict = {
            "user_id": lambda a :    a["id"],
            "user_name": lambda a:   a["name"],
            "user_email": lambda a:  a["email"]
        }
        res = {key:property_dict.get(key, None) for key in property_list}
        return res
