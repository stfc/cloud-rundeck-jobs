from .classes.list_hosts import ListHosts
from .classes.list_ips import ListIps
from .classes.list_servers import ListServers
from .classes.list_projects import ListProjects
from .classes.list_users import ListUsers
from .utils import CreateOpenstackConnection, OutputToConsole, OutputToFile, ValidateInputList


def Query(by, properties_list, criteria_list, sort_by_list, output_to_console=False, save=False, save_path="~/Openstack_Logs/output.csv", openstack_conn=None):
    '''
    Function to handle an openstack query

        Parameters:
            by (string}: openstack resource to search by
            properties_list ([string]): list of properties to get for each openstack resource found
            criteria_list ([string]): list of criteria/conditional arguments that make up the query
            sort_by_list ([string]): list of properties to sort the results by

        Optional Parameters:
            output_to_console (bool): flag to toggle print to console
            save (bool): flag to toggle save to txt file
            save_in (string): path to directory in which to save the txt file
            openstack_conn (openstack.connection.Connection object): user given openstack connection

        Returns:
            res ([{dict}]): list of dictionaries - query results
            (each dict in list representing a single compute resource)
            None: if query fails
    '''

    # if no user defined openstack connection given - create default one
    if not openstack_conn:
        openstack_conn = CreateOpenstackConnection()

    # validate by
    list_class = {
        "user": ListUsers,
        "server": ListServers,
        "project": ListProjects,
        "ip": ListIps,
        "host": ListHosts
    }.get(by, None)

    if not list_class:
        print("Search by condition {} is invalid".format(by))
        return None

    list_obj = list_class(openstack_conn)

    # validate properties_list
    properties_to_use, invalid = ValidateInputList(properties_list, list_obj.property_func_dict.keys())
    if invalid:
        print("Following properties are not valid: {}".format(invalid))
    if not properties_to_use:
        print("No properties given/valid - aborting")
        return None

    # validate criteria_list
    if criteria_list:
        criteria_names, invalid = ValidateInputList([criteria[0] for criteria in criteria_list], list_obj.criteria_func_dict.keys())
        if invalid:
            print("Following properties are not valid: \n {}".format(invalid))
        criteria_to_use = [(criteria[0], criteria[1:]) for criteria in criteria_list if criteria[0] in criteria_names]
    else:
        criteria_to_use = []
    # validate sort_by_list
    sort_by_to_use, invalid = ValidateInputList(sort_by_list, list_obj.property_func_dict.keys())
    if invalid:
        print("Following sort_by are not valid: \n {}".format(invalid))

    print("""Searching by resouce: {0} \nCriteria Selected: {1} \nProperties Selected: {2} \nSort By Selected: {3}""".format(by,
    criteria_to_use, properties_to_use, sort_by_to_use))

    # get results
    items = list_obj.listItems(criteria_to_use)
    if items:
        res = list_obj.getProperties(items, properties_to_use)

        if sort_by_to_use:
            res = sorted(res, key = lambda a: tuple(a[arg] for arg in sort_by_to_use))
        if output_to_console:
            OutputToConsole(res)
        if save:
            OutputToFile(save_path, res)

        return res