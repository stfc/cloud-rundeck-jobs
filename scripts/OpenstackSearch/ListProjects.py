from ListItems import ListItems

class ListProjects(ListItems):
    def __init__(self, conn):
        super().__init__(conn, lambda: conn.list_projects())

        self.criteria_func_dict.update({
            "enabled": lambda dict, args: dict["enabled"] == True,
            "not_enabled": lambda dict, args: dict["enabled"] == False,

            "description_contains": lambda dict, args: any(arg in dict["description"] for arg in args)
        })

        self.property_func_dict = {
            "project_id": lambda a :  a["id"],
            "project_name": lambda a: a["name"],
            "project_description": lambda a: a["description"]
        }
