from st2common.runners.base_action import Action
import sqlite3
import openstack

class DB_Action(Action):
    def run(self, **kwargs):
        """
        function that is run by stackstorm when the action is invoked
        :param kwargs: arguments for the database actions
        :return: (Status (Bool), Output <*>): tuple of action status (succeeded(T)/failed(F)) and the output
        """
        self.db = self.connect_to_database(kwargs["db_file_path"])
        self.db_cursor = self.db.cursor()
        self.conn = self.connect_to_openstack()

        # get appropriate database action to perform based on "submodule" argument
        fn = self.func.get(kwargs["submodule"])
        return fn(**{k: v for k, v in kwargs.items() if v is not None and k not in ["submodule", "db_file_path"]})

    def connect_to_openstack(self):
        """
        connect to openstack using the openstack sdk
        :return: openstack connection object
        """
        return openstack.connect()

    def connect_to_database(self, db_path):
        """
        connect to sqlite database that holds greenbone information
        :param db_path: file path to sqlite database
        :return: sqlite connection object
        """
        db = sqlite3.connect(db_path)
        db.row_factory = self.dict_factory
        return db

    def dict_factory(self, cursor, row):
        """
        function to return sqlite db query results as a dictionary
        :param cursor: sqlite cursor object
        :param row: query result row to output (list)
        :return: dictionary conversion of the row list. Key is the field name, and Value is the corresponding row value
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
