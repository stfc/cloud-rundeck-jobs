import datetime
import re

class ListItems:
    """
    Base class to list openstack resources

    Attributes
    ----------
    criteria_func_dict: dict
        stores generic query criteria options -
        criteria name (key) : function to evaluate generic criteria on a openstack resource(value)
                function (bool) - evaluate a generic openstack resource against a criteria

    property_func_dict: dict
        stores possible generic properties most openstack resource have
        property name (key) : function to retrieve property (value)
                function (string/int) - returns property value

    conn: (openstack.connection.Connection object)
        openstack connection object

    search_func: func()
        function that will retrieve all possible instances of an openstack resource
        (provided by subclasses)

    Methods
    --------
    listItems(criteria_list):
        method to list openstack resources
        returns list of resouces as a Munch.munch object

    getProperties(all_items_list, property_list):
        method to get certain properties for a list of openstack resources
        returns a list of dictionaries where each dictionary represents an
        openstack resource and its values for selected properties

    """
    def __init__(self, conn, search_func):
        '''constructor class'''
        self.conn = conn
        self.search_func = search_func
        self.criteria_func_dict = {
            "name": lambda dict, args: dict["name"] in args,
            "not_name": lambda dict, args: dict["name"] not in args,
            "name_contains": lambda dict, args: any(arg in dict["name"] for arg in args),
            "name_not_contains": lambda dict, args: any(arg not in dict["name"] for arg in args),

            "id": lambda dict, args: dict["id"] in args,
            "not_id": lambda dict, args: dict["id"] not in args,
        }

    def parseCriteria(self, criteria_list):
        '''
        Helper function to parse and validate a list of criteria
            Parameters:
                criteria_list [(criteria name, [args])] : list of tuples
                containing criteria name and list of arguments
            Returns:
                a sublist of criteria from criteria_list which are valid
                for the given openstack resource being queried
        '''
        res = []
        for key, args in criteria_list:
            func = lambda dict, key=key, args=args: self.getCriteriaFunc(key)(dict, args)
            if func:
                res.append(func)
            else:
                print("criteria name {} not found - ignoring".format(key))
        if not res:
            print("no criteria selected - getting all")
            res = [lambda dict: True]
        return res

    def parseProperties(self, property_list):
        '''
        Helper function to parse a list of properties
            Parameters:
                property_list [string] : list of property names
            Returns:
                a dictionary of {property name: function to get property} where all keys
                are a valid sublist of names from property_list
        '''
        return {key: self.getPropertyFunc(key) for key in property_list}

    def listItems(self, criteria_list):
        '''
        Function to list items by calling the function held in attribute search_func.
        Then filter by them by a set of criteria
            Parameters:
                criteria_list [(criteria name, [args])] : list of tuples
                containing criteria name and list of arguments
            Returns:
                [Munch.munch object] list of openstack resources
                that match all given criteria
        '''
        criteria_list = self.parseCriteria(criteria_list)
        """
        try:
            all_items = self.search_func()
        except Exception as e:
            print("error, could not get items")
            print(repr(e))
            return None
        """
        all_items = self.search_func()
        selected_items = []
        for i, item in enumerate(all_items):
            res = True
            for criteria in criteria_list:
                if not criteria(item):
                    res = False
            if res:
                selected_items.append(item)
        return selected_items

    def getProperties(self, all_items_list, property_list):
        '''
        Function to get the selected properties from a list of openstack resources
            Parameters:
                all_items_list [Munch.munch object]: list of openstack resources
                property_list [string]: list of property names to get

            Returns:
                [dict] list of dictionaries where each dict contains the properties
                specified in property_list for each openstack resource in all_items_list
        '''
        property_dict = self.parseProperties(property_list)

        res = []
        for item in all_items_list:
            output_dict = {}
            for key, val in property_dict.items():
                if val:
                    try:
                        output_dict[key] = val(item)
                    except Exception as e:
                        output_dict[key] = "not found"
            res.append(output_dict)
        return res

    def getCriteriaFunc(self, key):
        '''
            Helper function to get criteria function given the criteria name
            Parameters:
                key (string): criteria name
            Returns: (func) function that corresponds to criteria name
        '''
        return self.criteria_func_dict.get(key, None)

    def getPropertyFunc(self, key):
        '''
            Helper function to get property function given the property name
            Parameters:
                key (string): property name
            Returns: (func) function that corresponds to property name
        '''
        return self.property_func_dict.get(key, None)

    def isOlderThanXDays(self, created_at, days):
        '''
            Function to get if openstack resource is older than a given
            number of days
            Parameters:
                created_at (string): timestamp that represents date and time
                a resource was created
                days (int): number of days treshold

            Returns: (bool) True if older than days given else False
        '''
        return self.isCreatedAtOlderThanOffset(created_at, datetime.timedelta(days=int(days)).total_seconds())

    def isCreatedAtOlderThanOffset(self, created_at, time_offset_in_seconds):
        '''
            Helper function to get if openstack resource is older than a
            given number of seconds
            Parameters:
                created_at (string): timestamp that represents date and time
                a resource was created
                time_offset_in_seconds (int): number of seconds threshold
                
            Returns: (bool) True if older than days given else False
        '''
        offset_timestamp = (datetime.datetime.now()).timestamp() - time_offset_in_seconds
        created_at_datetime = datetime.datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ').timestamp()
        return offset_timestamp > created_at_datetime
