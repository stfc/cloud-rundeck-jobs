from ListItems import ListItems

class ListProjects(ListItems):
    ListItems.criteria_func_dict.update({
        "is_enabled": lambda dict, args: dict["enabled"] == True,
        "description_contains": lambda dict, args: any(arg in dict["description"] for arg in args)
    })

    property_func_dict = {
        "project_id": lambda a :  a["id"],
        "project_name": lambda a: a["name"],
        "project_description": lambda a: a["description"]
    }

    def __init__(self, conn, criteria_list, property_list):
        super().__init__(conn, lambda: conn.list_projects(),
                        criteria_list, property_list)
