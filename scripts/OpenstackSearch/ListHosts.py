from ListItems import ListItems

class ListHosts(ListItems):
    ListItems.criteria_func_dict.update({
        "status": lambda dict, args: dict["status"] in args,
        "not_status": lambda dict, args: dict["status"] not in args,

    })

    property_func_dict = {
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

    def __init__(self, conn, criteria_list, property_list):
        super().__init__(conn, lambda: conn.list_hypervisors(),
                        criteria_list, property_list)
