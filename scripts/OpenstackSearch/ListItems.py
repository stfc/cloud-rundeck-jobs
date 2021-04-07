import operator

class ListItems:
    def __init__(self, conn, search_func, criteria_func_list, properties_dict):
        self.conn = conn
        self.search_func = search_func
        self.criteria_list = criteria_func_list
        self.properties_dict = properties_dict

    def listItems(self):
        """
            List items by running a list function, and find all items that match a set of criteria
            list_func - function to get list of all items to search
            criteria_func_list - list of functions to search whole list of items by
        """
        try:
            all_items = self.search_func()
        except Exception as e:
            print("error, could not get items")
            print(repr(e))
            return None
        print("got all items")
        selected_items = []
        for item in all_items:
            res = True
            for criteria in self.criteria_list:
                if not criteria(item):
                    res = False
            if res:
                selected_items.append(item)
        print("got selected items")
        return selected_items

    def getProperties(self, all_items_list):
        """ function to get properties using openstack using corresponding id """
        res = []
        for item in all_items_list:
            output_dict = {}
            for key, val in self.properties_dict.items():
                if val:
                    try:
                        output_dict[key] = val(item)
                    except Exception as e:
                        output_dict[key] = "not found"
            res.append(output_dict)
        return res
