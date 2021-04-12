from ListItems import ListItems

class ListUsers(ListItems):
    ListItems.criteria_func_dict.update({
        "is_enabled": lambda dict, args: dict["enabled"] == True,
    })

    property_func_dict = {
        "user_id": lambda a :    a["id"],
        "user_name": lambda a:   a["name"],
        "user_email": lambda a:  a["email"]
    }

    def __init__(self, conn, criteria_list, property_list):
        super().__init__(conn, lambda: conn.list_users(), criteria_list, property_list)
