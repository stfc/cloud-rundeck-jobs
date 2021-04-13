import argparse
import csv
from tabulate import tabulate
import os.path
import openstack
import sys
import datetime

from ListHosts import ListHosts
from ListIps import ListIps
from ListServers import ListServers
from ListProjects import ListProjects
from ListUsers import ListUsers

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

        if not os.path.exists(filepath):
            os.makedirs(filepath)

        keys = results_dict_list[0].keys()
        timestamp = "{:%Y-%m-%d_%H:%M}".format(datetime.datetime.now())
        with open(filepath+"{}_search_output.txt".format(timestamp), "w", newline="\n") as output_file:
            writer = csv.DictWriter(output_file, keys)
            writer.writeheader()
            writer.writerows(results_dict_list)
    else:
        print("none found - no file made")

if __name__ == '__main__':
    # ARGPARSE BOILERPLATE CODE TO READ IN INPUTS
    parser = argparse.ArgumentParser(description='Get Information From Openstack')

    parser.add_argument("search_by", help="Search For Specific Resource Type",
    nargs=1, choices =["project", "host", "ip", "user", "server"])
    parser.add_argument('-s', "--select", nargs="+", help="properties to get")
    parser.add_argument('-w', "--where", nargs="+", action='append',
    help="selection policy", metavar=('policy', '*args'))

    parser.add_argument("--sort-by", nargs="+")

    parser.add_argument("--no-output", default=False, action="store_true")
    parser.add_argument("--save", default=False, action="store_true")
    parser.add_argument("--save-in", type=str, default="./Logs/")

    args = parser.parse_args()
    conn = openstack.connect(cloud_name="openstack", region_name="RegionOne")

    # get what to search by
    list_class = {
        "user": ListUsers,
        "server": ListServers,
        "project": ListProjects,
        "ip": ListIps,
        "host": ListHosts
    }.get(args.search_by[0], None)

    if list_class:
        list_obj = list_class(conn)

        # get all properties
        properties_list = []
        for property in args.select:
            if property not in list_obj.property_func_dict.keys():
                print("property called {} does not exist, ignoring".format(property[0]))
            else:
                properties_list.append(property)
        print("properties selected: {}".format(properties_list))
        if not properties_list:
            print("no properties valid - exiting")
            sys.exit(1)

        # get all criteria
        criteria_list = []
        if args.where:
            for criteria in args.where:
                if criteria[0] not in list_obj.criteria_func_dict.keys():
                    print("criteria called {} does not exist, ignoring".format(criteria[0]))
                else:
                    criteria_list.append((criteria[0], criteria[1:]))
        print("criteria selected: {}".format(criteria_list))

        # get sort_by criteria
        sort_by_args = []
        if args.sort_by:
            for arg in args.sort_by:
                if arg not in properties_list:
                    print("cannot sort by value {} - ignoring".format(arg))
                else:
                    sort_by_args.append(arg)
            print("properties to sort by {}".format(sort_by_args))
        else:
            print("no properties selected to sort by")

        # get results
        selected_items = list_obj.listItems(criteria_list)
        res = list_obj.getProperties(selected_items, properties_list)

        # handle output
        if sort_by_args:
            res = sorted(res, key = lambda a: tuple(a[arg] for arg in sort_by_args))
        if not args.no_output:
            OutputToConsole(res)
        if args.save:
            OutputToFile(args.save_in, res)
