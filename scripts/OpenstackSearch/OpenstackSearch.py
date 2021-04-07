import datetime
import re
import argparse
import csv
from tabulate import tabulate
import os.path
import openstack

from ListHosts import ListHosts
from ListIps import ListIps
from ListServers import ListServers
from ListProjects import ListProjects
from ListUsers import ListUsers



def isOlderThanXDays(server, days):
    return isServerOlderThanOffset(datetime.timedelta(days=int(days)).total_seconds(), server)

def isServerOlderThanOffset(time_offset_in_seconds, server):
    offset_timestamp = (datetime.datetime.now()).timestamp() - time_offset_in_seconds
    server_datetime = datetime.datetime.strptime(server["created_at"], '%Y-%m-%dT%H:%M:%SZ').timestamp()
    return offset_timestamp > server_datetime

def hasIllegalConnections(server):
    address_dict = server["addresses"]
    address_ips = []
    for key in address_dict.keys():
         for address in address_dict[key]:
            address_ips.append(address["addr"])
    return not areConnectionsLegal(address_ips)

def areConnectionsLegal(address_ips):
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

def OutputToConsole(results_dict_list):
    """ function to output a list of dictionaries to console """
    if results_dict_list:
        header = results_dict_list[0].keys()
        rows = [row.values() for row in results_dict_list]
        print(tabulate(rows, header))
    else:
        print("none found")

def OutputToFile(filepath, results_dict_list):
    """ function to output a list of dictionaries into a file """
    if results_dict_list:
        keys = results_dict_list[0].keys()
        with open(filepath, "w", newline="\n") as output_file:
            writer = csv.DictWriter(output_file, keys)
            writer.writeheader()
            writer.writerows(results_dict_list)
    else:
        print("none found - no file made")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get Information From Openstack')
    search_by_subparser = parser.add_subparsers(dest='search_by_subparser',
    description="Choose What to Search For:")

    user_parser = search_by_subparser.add_parser("user", help="Search By Users")
    user_parser.add_argument('-s', "--select", nargs="+", help="properties to get",
    choices=[
        "user_id","user_name","user_email"
    ])
    user_parser.add_argument('-w', "--where", nargs="+", action='append',
    help="selection policy", metavar=('policy', '*args'))

    server_parser = search_by_subparser.add_parser("server", help="Search By Servers")
    server_parser.add_argument('-s', "--select", nargs="+", help="properties to get",
    choices=[
        "user_id","user_name","user_email", "host_id", "host_name", "server_id",
        "server_name", "server_status","server_creation_date", "project_id",
        "project_name"
    ])
    server_parser.add_argument('-w', "--where", nargs="+", action='append',
    help="selection policy", metavar=('policy', '*args'))

    project_parser = search_by_subparser.add_parser("project", help="Search By Project")
    project_parser.add_argument('-s', "--select", nargs="+", help="properties to get",
    choices=[
        "project_id", "project_name", "project_description"
    ])
    project_parser.add_argument('-w', "--where", nargs="+", action='append',
    help="selection policy", metavar=('policy', '*args'))

    ip_parser = search_by_subparser.add_parser("ip", help="Search By Ips")
    ip_parser.add_argument('-s', "--select", nargs="+", help="properties to get",
    choices=[
        "ip_id","ip_fixed_address","ip_floating_address","ip_port_id",
        "project_id","project_name"
    ])
    ip_parser.add_argument('-w', "--where", nargs="+", action='append',
    help="selection policy", metavar=('policy', '*args'))

    host_parser = search_by_subparser.add_parser("host", help="Search By Host")
    host_parser.add_argument('-s', "--select", nargs="+", help="properties to get",
    choices=[
        "host_id","host_name","project_id","project_name"
    ])
    host_parser.add_argument('-w', "--where", nargs="+", action='append',
    help="selection policy", metavar=('policy', '*args'))

    args = parser.parse_args()
    conn = openstack.connect(cloud_name="openstack", region_name="RegionOne")

    list_class = {
        "user": ListUsers,
        "server": ListServers,
        "project": ListProjects,
        "ip": ListIps,
        "host": ListHosts
    }.get(args.search_by_subparser, None)

    criteria_list = []
    if args.where:
        for criteria in args.where:
            criteria_list.append((criteria[0], criteria[1:]))
    print(criteria_list)

    if list_class:
        list_obj = list_class(conn, criteria_list=criteria_list, property_list=args.select)
        selected_items = list_obj.listItems()
        res = list_obj.getProperties(selected_items)
        OutputToConsole(res)
