import sqlite3
import openstack

def GetAllUsers(db_cursor):
    db_cursor.execute('''SELECT DISTINCT User_ID FROM Hosts''')
    return db_cursor.fetchall()

def GetAllHostsForUser(db_cursor, user_id):
    """TODO: Check age of Host against Timestamp of Test"""
    db_cursor.execute('''SELECT Host_ID, IP, Resource_ID, Hostname FROM Hosts where User_ID = ?''', (user_id,))
    return db_cursor.fetchall()

def GetVulnerabilityInfoForHost(db_cursor, host_id):
    """

    TODO: Get CVEs
    vulns = db_cursor.fetchall()

    for vuln in vulns:
     db_cursor.execute('''SELECT CVEs.CVE, BIDs.BID, CERTs.CERT FROM CVEs
         INNER JOIN BIDs ON CVEs.NVT_OID = BIDs.NVT_OID
         INNER JOIN CERTs ON CVEs.NVT_OID = CERTs.NVT_OID
         WHERE NVT_OID = ?''', (vuln["NVT_OID"],))

     extras = db_cursor.fetchall()
     if extras:
    """

    db_cursor.execute('''SELECT NVT_OID, NVT_Name, Severity, Summary, Specific_Result, Solution FROM Greenbone_Vulnerabilities
        INNER JOIN Vulnerabilities ON Greenbone_Vulnerabilities.NVT_OID = Vulnerabilities.NVT_OID
        INNER JOIN Hosts ON Greenbone_Vulnerabilities.Host_ID = Hosts.Host_ID
        WHERE Hosts.Host_ID = ? 
        AND (Greenbone_Vulnerabilities.Severity = High OR Greenbone_Vulnerabilities.Severity = Critical) ''', (host_id,))
    return db_cursor.fetchall()

def GetVulnerabilityInfoForUser(db_cursor, user_id):
    return {
        host["IP"]:{
            "Hostname": host["Hostname"],
            "Resouce_ID": host["Resource_ID"],
            "Vulnerabilities": GetVulnerabilityInfoForHost(db_cursor, host["Host_ID"])
        } for host in GetAllHostsForUser(db_cursor, user_id)}

def PopulateEmailBody(user_info, vulnerability_info):
    host_message = ""
    vulnerability_num = 0
    host_num = 0
    for ip, host_info in vulnerability_info.items():
        if host_info["Vulnerabilities"]:
            host_message += """IP: {0}, Hostname: {1}, Openstack_ID, {2} \n""".format(ip, host_info["Hostname"], host_info["Resource_ID"])
            host_num += 1
            for i, vuln in enumerate(host_info["Vulnerabilities"]):
                vulnerability_num += 1
                host_message += """
                    NVT Name: {1}
                    Severity: {2}
                    Summary:
                    
                    {3}
                    
                    {4]
                    
                    Solution:
                    {5}\n
                """.format(vuln["NVT_OID"], vuln["NVT_Name"], vuln["Severity"], vuln["Summary"], vuln["Specific_Result"], vuln["Solution"])
    if host_message:
       return "{0} Vulnerabilities Found on Scanning {1} IPs For User {2}, ID {3}: \n\n {4}".format(
           str(vulnerability_num), str(host_num), ["name"], user_info["id"], host_message)
    return None

#ONLY GET HIGH, CRITICAL SEVERITY FOR NOW
#CHECK AGE OF VM BEFORE ASSIGNING USER_ID

def AggregateVulnerabilitiesPerUser(db_cursor):
    all_users = GetAllUsers(db_cursor)
    conn = openstack.connect()
    for user in all_users:
        user_info = conn.identity.find_user(user["User_ID"])
        vulnerabilities = GetVulnerabilityInfoForUser(db_cursor, user["User_ID"])
        message_body = PopulateEmailBody(user_info, vulnerabilities)
        if message_body:
            print(message_body)
            break
        #TODO POPULATE EMAIL BODY
        #TODO SEND EMAIL

"""

    aggregate vulnerabilities for each user_id

     FROM Greenbone_Vulnerabilities
    for each user_id (NOT NULL):
        - get host_ids
        - get all greenbone vulnerabilities matching host_id

        vulnerability corresponding
"""
