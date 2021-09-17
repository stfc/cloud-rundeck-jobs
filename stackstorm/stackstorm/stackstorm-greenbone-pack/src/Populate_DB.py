import csv
import openstack
import argparse
from Create_DB import ConnectToDatabase
from subprocess import Popen, PIPE
import os
import json
import re
import datetime

def ValidateFilePath(file_path):
    """
    Check that Greenbone csv exists and contains correct information
    :param file_path: (String) filepath to csv file with greenbone information
    :return:
    """
    assert os.path.exists(file_path), "file path {} does not exist".format(file_path)

    with open(file_path) as csv_file:
        reader = csv.reader(csv_file)
        headers = next(reader)
        assert all(header in headers for header in [
            "IP","Hostname","Port","Port Protocol","CVSS","Severity","Solution Type","NVT Name","Summary","Specific Result",
            "NVT OID","CVEs","Task ID","Task Name","Result ID","Impact","Solution","Affected Software/OS","Vulnerability Insight",
            "Vulnerability Detection Method","Product Detection Result","BIDs","CERTs", "Timestamp", "Other References"]), "incorrect headers in csv file given"

def GetIPDict():
    """
    Get a dictionaries of IPs corresponding to each Server_ID/Hypervisor_ID using openstack - required for looking up user_ids associated with each IP found in greenbone
    :return: Nested Dictionary of {Openstack Resource Name : {IP: Openstack Resource ID}}
    """
    p = Popen(sourcecmd+"openstack server list --all-projects --limit -1 -f json".format(), shell=True, stdout=PIPE, env=os.environ.copy())
    server_list = json.loads(p.communicate()[0])

    server_ip_dict = {}

    for s in server_list:
        for _, v in s["Networks"].items():
            for ip in v:
                # get all external IPs
                if not re.search("^192.168.", ip):
                    server_ip_dict[ip] = s["ID"]
    hv_ip_dict = {}
    conn = openstack.connect()
    for hv in conn.list_hypervisors():
        hv_ip_dict[hv["host_ip"]] = hv["id"]

    return {"server":server_ip_dict, "hypervisor":hv_ip_dict}

def PopulateDB(db, csv_path, ip_dicts):
    """
    Populate Database with information from greenbone scan
    :param db: SQLite Database object
    :param csv_path: (String) file path to greenbone scan results
    :param ip_dicts: (Nested Dictionaries) Information on IPs and associated Openstack Resources
        - For User_ID and Server Age lookup in openstack
    :return: None
    """

    db_cursor = db.cursor()
    # connect to openstack
    conn = openstack.connect()

    with open(csv_path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            # check if not already in DB
            db_cursor.execute('''SELECT * FROM Vulnerabilities WHERE NVT_OID = ?''', (row["NVT OID"],))
            vuln = db_cursor.fetchone()
            if not vuln:
                # insert into table
                db_cursor.execute('''INSERT INTO Vulnerabilities
                (NVT_OID, NVT_Name, Port, Protocol, Severity, Solution_Type,
                Summary, Specific_Result, Solution, Impact, Detection_Method,
                Insight, Affected_Software, Product_Detection_Result,
                Other_References) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                  (row["NVT OID"], row["NVT Name"], row["Port"], row["Port Protocol"], row["Severity"],
                                   row["Solution Type"], row["Summary"], str(row["Specific Result"]), row["Solution"],
                                   row["Impact"], row["Vulnerability Detection Method"], row["Vulnerability Insight"],
                                   row["Affected Software/OS"], row["Product Detection Result"], row["Other References"]
                                   ,))

                # parse and insert extra information into DB iteratively (BIDs, CVEs, CERTs) if available
                if row["CVEs"]:
                    cve_list = row["CVEs"].split(",")
                    for cve in cve_list:
                        db_cursor.execute('''INSERT INTO CVEs (NVT_OID, CVE) VALUES (?,?)''', (row["NVT OID"], cve,))

                if row["BIDs"]:
                    bid_list = row["BIDs"].split(",")
                    for bid in bid_list:
                        db_cursor.execute('''INSERT INTO BIDs (NVT_OID, BID) VALUES (?,?)''', (row["NVT OID"], bid,))

                if row["CERTs"]:
                    cert_list = row["CERTs"].split(",")
                    for cert in cert_list:
                        db_cursor.execute('''INSERT INTO CERTs (NVT_OID, CERT) VALUES (?,?)''', (row["NVT OID"], cert,))

            # Add metadata entry - if not exists
            db_cursor.execute('''SELECT * FROM Metadata WHERE Task_ID = ?''', (row["Task ID"],))
            task = db_cursor.fetchone()
            if not task:
                db_cursor.execute('''INSERT INTO Metadata (Task_ID, Task_Name) VALUES(?,?)''', (row["Task ID"], row["Task Name"],))

            # Check if IP is "Active" - currently being used by same server and that server is running

            # If Server younger than scan data - Server Rebuilt/IP has been reassigned
            #   - set IP_Status as "Server_Changed"

            # If Server not running - set IP_Status as "Inactive"
            ip_status = "Active"
            for type, ip_dict in ip_dicts.items():
                id = ip_dict.get(row["IP"], None)
                if id:
                    user_id = {
                        "server":lambda id: conn.compute.find_server(id)["user_id"],
                        "hypervisor":lambda id: None
                    }.get(type, lambda id: None)(id)

                    # if the ip has been reassigned recently
                    if type == "server":
                        scan_timestamp = datetime.datetime.strptime(row["Timestamp"], '%Y-%m-%dT%H:%M:%SZ').timestamp()
                        vm_creation_timestamp = datetime.datetime.strptime(conn.compute.find_server(id)["created_at"], '%Y-%m-%dT%H:%M:%SZ').timestamp()
                        if scan_timestamp < vm_creation_timestamp:
                            ip_status = "Server Changed"
                    break
            if not id:
                print("IP {0} (Hostname {1}) NOT FOUND in Openstack - classing Inactive".format(row["IP"],
                                                                                                row["Hostname"]))
                user_id = None
                ip_status = "Inactive"


            db_cursor.execute('''SELECT IP FROM Hosts WHERE IP = ?''',
                              (row["IP"],))
            ip = db_cursor.fetchone()
            if not ip:
                db_cursor.execute('''INSERT INTO Hosts (Resource_ID, IP, Hostname, User_ID) VALUES(?,?,?,?)''',
                                  (id, row["IP"], row["Hostname"], user_id,))

            db_cursor.execute('''INSERT INTO Greenbone_Vulnerabilities (Result_ID, Timestamp, IP_Status, IP, NVT_OID, Task_ID) VALUES(?,?,?,?,?,?)''',
                              (row["Result ID"], row["Timestamp"], ip_status, row["IP"], row["NVT OID"], row["Task ID"],))
            db.commit()

if __name__ == "__main__":
    sourcecmd = ". /etc/openstack/openrc/admin-openrc.sh;"

    parser = argparse.ArgumentParser(description="Populate Greenbone DB")
    parser.add_argument("--file-path", nargs=1, help="file path to greenbone csv file")
    args = parser.parse_args()
    print(args.file_path[0])
    ValidateFilePath(args.file_path[0])

    db = ConnectToDatabase("Greenbone.db")
    PopulateDB(db, args.file_path[0], GetIPDict())
