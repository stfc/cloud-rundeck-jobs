from .list_items import ListItems

class ListHosts(ListItems):
    """
    A class to list hosts (hypervisors): Inherits from ListItems

    Attributes
    ----------
    criteria_func_dict: dict
        stores possible query criteria options -
        criteria name (key) : function to evaluate a criteria on host (value)
                function (bool) - evaluate 'host' properties against criteria
                updates ListItems criteria_func_dict

    property_func_dict: dict
        stores possible host property options
        property name (key) : function to retrieve property (value)
                function (string/int) - returns property value from a 'host' dictionary
    """
    def __init__(self, conn):
        ''' constructor class '''
        super().__init__(conn, lambda: conn.list_hypervisors())

        self.criteria_func_dict.update({
            "status": lambda dict, args: dict["status"] in args,
            "not_status": lambda dict, args: dict["status"] not in args,

        })

        self.property_func_dict = {
            "host_id": lambda a : a["id"],
            "host_name":lambda a : a["name"],
            "host_status": lambda a : a["status"],
            "host_state": lambda a: a["host_state"],
            "host_ip": lambda a: a["host_ip"],

            "disk_available": lambda a: a["disk_available"],
            "local_disk_used": lambda a: a["local_disk_used"],
            "local_disk_size": lambda a: a["local_disk_size"],
            "local_disk_free": lambda a: a["local_disk_free"],

            "memory_used": lambda a: a["memory_used"],
            "memory_max": lambda a: a["memory_size"],
            "memory_free": lambda a: a["memory_free"],

            "running_vms": lambda a: a["running_vms"],

            "vcpus_used": lambda a: a["vcpus_used"],
            "vcpus_max": lambda a: a["vcpus"],
        }
