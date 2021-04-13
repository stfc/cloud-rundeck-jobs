from ListItems import ListItems

class ListUsers(ListItems):
    def __init__(self, conn):
        super().__init__(conn, lambda: conn.list_users())

        self.criteria_func_dict.update({
            "enabled": lambda dict, args: dict["enabled"] == True,
            "not_enabled": lambda dict, args: dict["enabled"] == False,
        })

        self.property_func_dict = {
            "user_id": lambda a :    a["id"],
            "user_name": lambda a:   a["name"],
            "user_email": lambda a:  a["email"]
        }
