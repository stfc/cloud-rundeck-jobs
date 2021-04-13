from ListItems import ListItems
import re

class ListServers(ListItems):
    def __init__(self, conn):
        super().__init__(conn, lambda: conn.list_servers(all_projects=True))

        self.criteria_func_dict.update({
            "status": lambda dict, args: dict["status"] in args,
            "not_status": lambda dict, args: dict["status"] not in args,

            "older_than": lambda dict, args: self.isOlderThanXDays(dict, days = args[0]),
            "not_older_than": lambda dict, args: not self.isOlderThanXDays(dict, days = args[0]),

            "has_illegal_connections": lambda dict, args: self.hasIllegalConnections(dict),

            "user_id": lambda dict, args: dict["user_id"] in args,
            "not_user_id": lambda dict, args: dict["user_id"] not in args,
            "user_name": lambda dict, args: self.conn.identity.find_user(dict["user_id"])["name"] in args,
            "not_user_name": lambda dict, args: self.conn.identity.find_user(dict["user_id"])["name"] not in args,
            "user_name_contains": lambda dict, args: any(arg in self.conn.identity.find_user(dict["user_id"])["name"] for arg in args),
            "user_name_not_contains": lambda dict, args: any(arg not in self.conn.identity.find_user(dict["user_id"])["name"] for arg in args),

            "host_id": lambda dict, args: dict["host_id"] in args,
            "not_host_id": lambda dict, args: dict["host_id"] not in args,
            "host_name": lambda dict, args: dict["hypervisor_hostname"] in args,
            "not_host_name": lambda dict, args: dict["hypervisor_hostname"] not in args,
            "host_name_contains": lambda dict, args: any(arg in dict["hypervisor_hostname"] for arg in args),
            "host_name_not_contains": lambda dict, args: any(arg not in dict["hypervisor_hostname"] for arg in args),


        })

        self.property_func_dict = {
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



    def hasIllegalConnections(self, server):
        address_dict = server["addresses"]
        address_ips = []
        for key in address_dict.keys():
             for address in address_dict[key]:
                address_ips.append(address["addr"])
        return not self.areConnectionsLegal(address_ips)

    def areConnectionsLegal(self, address_ips):
        if len(address_ips) == 1:
            return True

        # if list contains ip beginning with 172.16 - all must contain 172.16
        # else allowed
        # turn a flag on when ip other than 172.16 detected.
        # if then detected, flag as illegal

        i_flag = False
        for address in address_ips:
            if re.search("^172.16", address):
                if i_flag:
                    return False
            else:
                if not i_flag:
                    i_flag = True
        return True
