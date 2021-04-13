import operator
import datetime
import datetime
import re

class ListItems:
    def __init__(self, conn, search_func):
        """
            search_func - function to get list of all items
            criteria_list - list of functions to filter whole list of items (all return True/False)
            properties_dict - dictionary of {property name:function to get property}
        """
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
        """ function to parse a list of criteria tuples (criteria name, args (dictionary)) """
        res = []
        for key, args in criteria_list:
            func = lambda dict: self.getCriteriaFunc(key)(dict, args=args)
            if func:
                res.append(func)
            else:
                print("criteria name {} not found - ignoring".format(key))
        if not res:
            print("no criteria selected - getting all")
            res = [lambda dict: True]
        return res

    def parseProperties(self, property_list):
        """ function to parse a list of properties """
        res = {key: self.getPropertyFunc(key) for key in property_list}
        return res

    def listItems(self, criteria_list):
        """ List items by running the list function, and filter by all items that match a set of criteria found in criteria_list """

        criteria_list = self.parseCriteria(criteria_list)
        try:
            all_items = self.search_func()
        except Exception as e:
            print("error, could not get items")
            print(repr(e))
            return None

        selected_items = []
        for item in all_items:
            res = True
            for criteria in criteria_list:
                if not criteria(item):
                    res = False
            if res:
                selected_items.append(item)
        return selected_items

    def getProperties(self, all_items_list, property_list):
        """ function to get properties using openstack using corresponding id """
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
        return self.criteria_func_dict.get(key, None)

    def getPropertyFunc(self, key):
        return self.property_func_dict.get(key, None)

    def isOlderThanXDays(self, dict, days):
        return self.isCreatedAtOlderThanOffset(dict, datetime.timedelta(days=int(days)).total_seconds())

    def isCreatedAtOlderThanOffset(self, dict, time_offset_in_seconds):
        offset_timestamp = (datetime.datetime.now()).timestamp() - time_offset_in_seconds
        created_at_datetime = datetime.datetime.strptime(dict["created_at"], '%Y-%m-%dT%H:%M:%SZ').timestamp()
        return offset_timestamp > created_at_datetime
