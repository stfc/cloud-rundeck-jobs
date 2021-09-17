import os
import csv
import re
import json
import datetime
from subprocess import Popen, PIPE
from DB_Action import DB_Action


class CreateDB(DB_Action):
    def __init__(self, *args, **kwargs):
        """Constructor class"""

        self.func = {
            "create_tables": self.create_tables,
            "populate_db": self.populate_db
        }

    def create_tables(self, **kwargs):
        """
        method to create database tables and define db structure
        :param kwargs: options for db creation
        :return: (status (boolean), reason (string))
        """
        try:
            self.db_cursor.execute("PRAGMA foreign_keys = 3")
            self.db_cursor.executescript('''
                CREATE TABLE IF NOT EXISTS Vulnerabilities(
                    NVT_OID                     VARCHAR(30)     PRIMARY KEY,
                    NVT_Name                    VARCHAR(255)    NOT NULL,
                    Port                        INTEGER         NULL,
                    Protocol                    TEXT CHECK( Protocol IN ('tcp', 'udp', NULL))               NULL,
                    Severity                    TEXT CHECK( Severity IN ('Log','Low','Medium','High'))      NOT NULL,
                    Solution_Type               VARCHAR(255)    NULL,
                    Summary                     TEXT            NOT NULL,
                    Specific_Result             TEXT            NOT NULL,
                    Solution                    TEXT            NULL,
                    Impact                      TEXT            NULL,
                    Detection_Method            TEXT            NOT NULL,
                    Insight                     TEXT            NULL,
                    Affected_Software           TEXT            NULL,
                    Product_Detection_Result    TEXT            NULL,
                    Other_References            TEXT            NULL
                );
    
                CREATE TABLE IF NOT EXISTS CVEs(
                    NVT_OID     VARCHAR(30)     NOT NULL,
                    CVE         VARCHAR(255)    NOT NULL,
                    FOREIGN KEY(NVT_OID) REFERENCES Vulnerabilities(NVT_OID)
                );
    
                CREATE TABLE IF NOT EXISTS BIDs(
                    NVT_OID     VARCHAR(30)     NOT NULL,
                    BID         VARCHAR(255)    NOT NULL,
                    FOREIGN KEY(NVT_OID) REFERENCES Vulnerabilities(NVT_OID)
                );
    
                CREATE TABLE IF NOT EXISTS CERTs(
                    NVT_OID     VARCHAR(30)     NOT NULL,
                    CERT        VARCHAR(255)    NOT NULL,
                    FOREIGN KEY(NVT_OID) REFERENCES Vulnerabilities(NVT_OID)
                );
    
                CREATE TABLE IF NOT EXISTS Hosts(
                    IP          VARCHAR(255)    PRIMARY KEY,
                    Resource_ID VARCHAR(255)    NULL,
                    Hostname    VARCHAR(255)    NULL,
                    User_ID     VARCHAR(255)    NULL
                );
    
                CREATE TABLE IF NOT EXISTS Metadata(
                    Task_ID     VARCHAR(255)    PRIMARY KEY,
                    Task_Name   VARCHAR(255)    NOT NULL
                );
    
                CREATE TABLE IF NOT EXISTS Greenbone_Vulnerabilities(
                    Result_ID   VARCHAR(255)    PRIMARY KEY,
                    Timestamp   TEXT            NOT NULL,
                    IP_Status   TEXT CHECK ( IP_Status IN ('Active', 'Inactive', 'Server Changed')) Not NULL Default 'Active',
                    IP          VARCHAR(255)    Not NULL,
                    NVT_OID     VARCHAR(30)     NOT NULL,
                    Task_ID     VARCHAR(255)    NOT NULL,
                    FOREIGN KEY(IP) REFERENCES Hosts(IP),
                    FOREIGN KEY(NVT_OID) REFERENCES Vulnerabilities(NVT_OID),
                    FOREIGN KEY(Task_ID) REFERENCES Metadata(Task_ID)
                );
    
                ''')
            self.db.commit()
        except Exception as e:
            return False, repr(e)
        return True, "Creation Successful"

    def validate_file_path(self, file_path):
        """
          Check that Greenbone csv exists and contains correct information
          :param file_path: (String) filepath to csv file with greenbone information
          :return: (status (boolean)
          """
        assert os.path.exists(file_path), "file path {} does not exist".format(file_path)

        with open(file_path) as csv_file:
            reader = csv.reader(csv_file)
            headers = next(reader)
            if not all(header in headers for header in [
                "IP", "Hostname", "Port", "Port Protocol", "CVSS", "Severity", "Solution Type", "NVT Name", "Summary",
                "Specific Result",
                "NVT OID", "CVEs", "Task ID", "Task Name", "Result ID", "Impact", "Solution", "Affected Software/OS",
                "Vulnerability Insight",
                "Vulnerability Detection Method", "Product Detection Result", "BIDs", "CERTs", "Timestamp",
                "Other References"]):
                return False
        return True

    def get_ips_from_openstack(self):
        """
           Get a dictionaries of IPs corresponding to each Server_ID/Hypervisor_ID using openstack - required for looking up user_ids associated with each IP found in greenbone
           :return: Nested Dictionary of {Openstack Resource Name : {IP: Openstack Resource ID}}
           """

        # get all servers - via bash cmd
        sourcecmd = ". /etc/openstack/openrc/admin-openrc.sh;"
        p = Popen(sourcecmd + "openstack server list --all-projects --limit -1 -f json".format(), shell=True,
                  stdout=PIPE, env=os.environ.copy())
        server_list = json.loads(p.communicate()[0])

        # find all networks
        server_ip_dict = {}

        for s in server_list:
            for _, v in s["Networks"].items():
                for ip in v:
                    # get all external IPs
                    if not re.search("^192.168.", ip):
                        server_ip_dict[ip] = s["ID"]

        hv_ip_dict = {}
        for hv in self.conn.list_hypervisors():
            hv_ip_dict[hv["host_ip"]] = hv["id"]

        return {"server": server_ip_dict, "hypervisor": hv_ip_dict}

    def populate_db(self, **kwargs):
        """
        Populate Database with information from greenbone scan
        :param db: SQLite Database object
        :param csv_path: (String) file path to greenbone scan results
        :param ip_dicts: (Nested Dictionaries) Information on IPs and associated Openstack Resources
            - For User_ID and Server Age lookup in openstack
        :return: (status (boolean), reason (string))
        """
        assert "csv_path_list" in kwargs.keys(), "No greenbone csv file paths given"
        ip_dicts = self.get_ips_from_openstack()

        for csv_path in kwargs["csv_path_list"]:
            if not self.validate_file_path(csv_path):
                print("filepath given {0} is not valid".format("csv_path_list"))
                break

            with open(csv_path) as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    # check if not already in DB
                    self.db_cursor.execute('''SELECT * FROM Vulnerabilities WHERE NVT_OID = ?''', (row["NVT OID"],))
                    vuln = self.db_cursor.fetchone()

                    if not vuln:
                        # insert into table
                        self.db_cursor.execute('''INSERT INTO Vulnerabilities
                        (NVT_OID, NVT_Name, Port, Protocol, Severity, Solution_Type,
                        Summary, Specific_Result, Solution, Impact, Detection_Method,
                        Insight, Affected_Software, Product_Detection_Result,
                        Other_References) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                          (row["NVT OID"], row["NVT Name"], row["Port"], row["Port Protocol"],
                                           row["Severity"],
                                           row["Solution Type"], row["Summary"], str(row["Specific Result"]),
                                           row["Solution"],
                                           row["Impact"], row["Vulnerability Detection Method"],
                                           row["Vulnerability Insight"],
                                           row["Affected Software/OS"], row["Product Detection Result"],
                                           row["Other References"]
                                           ,))

                        # parse and insert extra information into DB iteratively (BIDs, CVEs, CERTs) if available
                        if row["CVEs"]:
                            cve_list = row["CVEs"].split(",")
                            for cve in cve_list:
                                self.db_cursor.execute('''INSERT INTO CVEs (NVT_OID, CVE) VALUES (?,?)''',
                                                  (row["NVT OID"], cve,))

                        if row["BIDs"]:
                            bid_list = row["BIDs"].split(",")
                            for bid in bid_list:
                                self.db_cursor.execute('''INSERT INTO BIDs (NVT_OID, BID) VALUES (?,?)''',
                                                  (row["NVT OID"], bid,))

                        if row["CERTs"]:
                            cert_list = row["CERTs"].split(",")
                            for cert in cert_list:
                                self.db_cursor.execute('''INSERT INTO CERTs (NVT_OID, CERT) VALUES (?,?)''',
                                                  (row["NVT OID"], cert,))

                    # Add metadata entry - if not exists
                    self.db_cursor.execute('''SELECT * FROM Metadata WHERE Task_ID = ?''', (row["Task ID"],))
                    task = self.db_cursor.fetchone()
                    if not task:
                        self.db_cursor.execute('''INSERT INTO Metadata (Task_ID, Task_Name) VALUES(?,?)''',
                                          (row["Task ID"], row["Task Name"],))

                    # Check if IP is "Active" - currently being used by same server and that server is running

                    # If Server younger than scan data - Server Rebuilt/IP has been reassigned
                    #   - set IP_Status as "Server_Changed"

                    # If Server not running - set IP_Status as "Inactive"
                    ip_status = "Active"
                    for type, ip_dict in ip_dicts.items():
                        id = ip_dict.get(row["IP"], None)
                        if id:
                            user_id = {
                                "server": lambda id: self.conn.compute.find_server(id)["user_id"] if self.conn.compute.find_server(id) else None,
                                "hypervisor": lambda id: None
                            }.get(type, lambda id: None)(id)

                            # if the ip has been reassigned recently
                            if type == "server":
                                scan_timestamp = datetime.datetime.strptime(row["Timestamp"],
                                                                            '%Y-%m-%dT%H:%M:%SZ').timestamp()
                                vm_creation_timestamp = datetime.datetime.strptime(
                                    self.conn.compute.find_server(id)["created_at"], '%Y-%m-%dT%H:%M:%SZ').timestamp()
                                if scan_timestamp < vm_creation_timestamp:
                                    ip_status = "Server Changed"
                            break
                    if not id:
                        #print("IP {0} (Hostname {1}) NOT FOUND in Openstack - classing Inactive".format(row["IP"],
                        #                                                                                row["Hostname"]))

                        user_id = None
                        ip_status = "Inactive"

                    self.db_cursor.execute('''SELECT IP FROM Hosts WHERE IP = ?''',
                                      (row["IP"],))
                    ip = self.db_cursor.fetchone()
                    if not ip:
                        self.db_cursor.execute('''INSERT INTO Hosts (Resource_ID, IP, Hostname, User_ID) VALUES(?,?,?,?)''',
                                          (id, row["IP"], row["Hostname"], user_id,))

                    self.db_cursor.execute(
                        '''INSERT INTO Greenbone_Vulnerabilities (Result_ID, Timestamp, IP_Status, IP, NVT_OID, Task_ID) VALUES(?,?,?,?,?,?)''',
                        (row["Result ID"], row["Timestamp"], ip_status, row["IP"], row["NVT OID"], row["Task ID"],))
                    self.db.commit()

        return True, "DB populated"


