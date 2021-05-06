from tabulate import tabulate
import csv
import os.path
import openstack

'''
Utility functions for query_openstack module

Functions:
    CreateOpenstackConnection(string, string)
    ValidateInputList([string], [string])
    OutputToConsole([{key:value}])
    OutputToFile([{key:value}])
'''

def CreateOpenstackConnection(cloud_name="openstack", region_name="RegionOne"):
    '''
        Get Openstack connection
            (gets properties from ~/.config/openstack/clouds.yaml)

            Parameters:
                    cloud_name (string): name of cloud in yaml script to use (default 'openstack')
                    region_name (string): name of region in yaml script to use (defailt 'RegionOne')
            Returns: (openstack.connection.Connection object): openstack connection object
    '''
    return openstack.connect(cloud=cloud_name, region_name=region_name)

def ValidateInputList(list_to_check, valid_list):
    '''
        Separate a list_to_check into valid and invalid lists - based on contents of valid_list

            Parameters:
                    list_to_check ([string]): list to validate
                    valid_list ([string]): list of all valid examples
            Returns: ([list], [list]): tuple of two distinct sublists containing valid
            or invalid entries respectively
    '''
    valid, invalid = [],[]
    if list_to_check:
        for property in list_to_check:
            invalid.append(property) if property not in valid_list \
            else valid.append(property)
    return valid, invalid

def OutputToConsole(results_dict_list):
    '''
        Output a result of query to console - prints table using tabulate

            Parameters:
                results_dict_list (list of dictionaries: [{}]) - a list of dictionaries
                representing the query results
            Returns: None
    '''
    if results_dict_list:
        header = results_dict_list[0].keys()
        rows = [row.values() for row in results_dict_list]
        print(tabulate(rows, header))
    else:
        print("none found")

def OutputToFile(dir_path, results_dict_list):
    '''
        Write results of query into a file
            - csv format:
                - whitespace as delimeter
                - saves as {TIMESTAMP}_search_output.txt where timestamp is the
                time the file was written

            Parameters:
                dir_path (string) - a path to directory in which to save file
            Returns: None
    '''
    if results_dict_list:

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        keys = results_dict_list[0].keys()
        timestamp = "{:%Y-%m-%d_%H:%M}".format(datetime.datetime.now())
        with open(dir_path+"{}_search_output.txt".format(timestamp), "w", newline="\n") as output_file:
            writer = csv.DictWriter(output_file, keys)
            writer.writeheader()
            writer.writerows(results_dict_list)
    else:
        print("none found - no file made")
