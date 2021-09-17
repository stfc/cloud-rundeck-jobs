from DB_Action import DB_Action
import csv

class QueryDB(DB_Action):
    def __init__(self, *args, **kwargs):
        """Constructor class"""
        super().__init__(*args, **kwargs)

        # lists possible functions that could be run as an action
        self.func = {
            "get_user_ids": self.get_user_ids,
            "get_info_for_user": self.get_info_for_user,
            "get_info_for_admin": self.get_info_for_admin,
            "create_csv_file": self.create_csv_file
        }

    def populate_vuln_dict(self, query_res):
        """
        Group together and create a dictionary of vulnerabilities for each ip from an sql query
        :param query_res: dictionary representing an sql query listing vulnerability information
        :return: vuln_dict - dictionary {ip:[vulnerability dictionary list]}
        """
        vuln_dict = {}
        for vuln in query_res:
            host_ip = vuln.pop("IP")
            if host_ip in vuln_dict.keys():
                vuln_dict[host_ip].append(vuln)
            else:
                vuln_dict[host_ip] = [vuln]
        return vuln_dict

    def query_for_vulnerabilities(self, user_id=None):
        """
        Helper method to return vulnerabilities for a given user_id (if provided a user_id) or vulnerabilities for admin
        (Vulnerabilities with no associated user, Inactive VMs/Hypervisors, or ones that have "Server Changed" Status)
        :param user_id: Either None or a User_ID string
        :return: query_res - a list of dictionaries containing vulnerability info
        """
        # if a user_id is not given - find vulnerabilities for all IPs that have status Inactive/Server Changed,
        # and IPs that do not have an associated user_id
        if not user_id:
            try:
                self.db_cursor.execute('''
                    SELECT DISTINCT
                        Greenbone_Vulnerabilities.IP AS IP,
                        Greenbone_Vulnerabilities.IP_Status AS IP_Status,
                        Hosts.Hostname AS Hostname,
                        Hosts.User_ID AS User_ID,
                        Vulnerabilities.NVT_Name AS NVT_Name, 
                        Vulnerabilities.Severity AS Severity, 
                        Vulnerabilities.Summary AS Summary, 
                        Vulnerabilities.Specific_Result AS Specific_Result, 
                        Vulnerabilities.Solution AS Solution 
                    FROM Greenbone_Vulnerabilities
                    INNER JOIN Vulnerabilities ON Greenbone_Vulnerabilities.NVT_OID = Vulnerabilities.NVT_OID
                    INNER JOIN Hosts ON Greenbone_Vulnerabilities.IP = Hosts.IP
                    WHERE (Greenbone_Vulnerabilities.IP_Status = 'Inactive' 
                        OR Greenbone_Vulnerabilities.IP_Status = 'Server Changed' 
                        OR Hosts.User_ID = NULL)
                    AND (Vulnerabilities.Severity = 'High' 
                        OR Vulnerabilities.Severity = 'Critical')
                    ORDER BY Greenbone_Vulnerabilities.IP ASC;
                ''')
                query_res = self.db_cursor.fetchall()
            except Exception as e:
                raise Exception("Error Getting Information From Database {0}".format(e))
        # if a user_id is given - find vulnerabilities for that user only
        else:
            try:
                self.db_cursor.execute('''
                        SELECT DISTINCT
                            Greenbone_Vulnerabilities.IP AS IP,
                            Hosts.User_ID AS User_ID,
                            Hosts.Hostname AS Hostname,
                            Vulnerabilities.NVT_Name AS NVT_Name, 
                            Vulnerabilities.Severity AS Severity, 
                            Vulnerabilities.Summary AS Summary, 
                            Vulnerabilities.Specific_Result AS Specific_Result, 
                            Vulnerabilities.Solution AS Solution 
                        FROM Greenbone_Vulnerabilities
                        INNER JOIN Vulnerabilities ON Greenbone_Vulnerabilities.NVT_OID = Vulnerabilities.NVT_OID
                        INNER JOIN Hosts ON Greenbone_Vulnerabilities.IP = Hosts.IP
                        WHERE Hosts.User_ID = ?
                        AND Greenbone_Vulnerabilities.IP_Status = 'Active'
                        AND (Vulnerabilities.Severity = 'High' OR Vulnerabilities.Severity = 'Critical')
                        ORDER BY Greenbone_Vulnerabilities.IP ASC;
                    ''', (user_id,))
                query_res = self.db_cursor.fetchall()
            except Exception as e:
                raise Exception("Error Getting Information From Database {0}".format(e))
        return query_res

    def get_user_ids(self, **kwargs):
        """
        method to get all user_ids found in the db that have vulnerabilities associated with them
        :param kwargs: (None)
        :return: (status (boolean), user_id_list ([String]))
        """
        try:
            self.db_cursor.execute('''                
                SELECT DISTINCT Hosts.User_ID AS User_ID 
                FROM Greenbone_Vulnerabilities
                INNER JOIN Vulnerabilities ON Greenbone_Vulnerabilities.NVT_OID = Vulnerabilities.NVT_OID
                INNER JOIN Hosts ON Greenbone_Vulnerabilities.IP = Hosts.IP
                WHERE Greenbone_Vulnerabilities.IP_Status = 'Active'
                AND (Vulnerabilities.Severity = 'High' OR Vulnerabilities.Severity = 'Critical')
            ''')
            query_res = self.db_cursor.fetchall()
        except Exception as e:
            raise Exception("Error Getting Information From Database: {0}".format(e))
        if not query_res:
            raise ValueError("No User_IDs Found in database")
        user_id_list = [user_id["User_ID"] for user_id in query_res if user_id["User_ID"]]
        return True, user_id_list

    def get_info_for_admin(self, **kwargs):
        """
        method to get info of all vulnerabilities detected on all hosts with specific IP status
        :param kwargs: (get_html - whether to return the informtiion as html file or not)
        :return: (status (boolean), message_body (string))
        """
        html_body = ""
        plain_text_body = ""
        found_vulns = False
        for ip, vulns in self.populate_vuln_dict(self.query_for_vulnerabilities()).items():
            found_vulns = True
            hostname = vulns[0]["Hostname"]
            ip_status = vulns[0]["IP_Status"]
            user_id = vulns[0]["User_ID"]
            user_info = self.conn.identity.find_user(user_id) if user_id else None
            html_body += """
            <p>&nbsp;</p>
            <table style="width: 650px">
                <tbody>
                    <tr>
                        <th>IP</th>
                        <th>{0}</th>
                    </tr>
                    <tr>
                        <th>IP Status</th>
                        <th>{1}</th>
                    </tr>
                    <tr>
                        <th>Hostname</th>
                        <th>{2}</th>
                    </tr>
                    <tr>
                        <th>User Name</th>
                        <th>{3}</th>
                    </tr>
                    <tr>
                        <th>User Email</th>
                        <th>{4}</th>
                    </tr>
                </tbody>
            </table>
            """.format(
                ip, ip_status, hostname, user_info["name"] if user_info else "Not Found", user_info["email"] if user_info else "Not Found"
            )

            plain_text_body += """IP: {0}\nIP Status: {1}\nHostname: {2}\nUser_Name: {3}\nUser_Email: {4}\n\n""".format(
                ip, ip_status, hostname, user_info["name"] if user_info else "Not Found", user_info["email"] if user_info else "Not Found")

            text, html = self.populate_vulns(vulns)
            plain_text_body += text
            html_body += html

        message_body = html_body if kwargs["get_html"] else plain_text_body
        if found_vulns:
            return True, message_body
        return True, "query resulted in no output"


    def get_info_for_user(self, **kwargs):
        """
        method to get info of all active vulnerabilities on hosts associated with a specified User_ID
        :param kwargs: user_id - get vulnerabilities for specified user
        :return: (status (boolean), message_body (string))
        """
        user_info = self.conn.identity.find_user(kwargs["user_id"])
        plain_text_body = ""
        html_body = ""
        found_vulns = False
        for ip, vulns in self.populate_vuln_dict(self.query_for_vulnerabilities(kwargs["user_id"])).items():
            found_vulns = True
            hostname = vulns[0]["Hostname"]

            html_body +=  """\
            <table style="width: 650px">
                <tbody>
                    <tr>
                        <th>IP</th>
                        <th>{0}</th>
                    </tr>
                    <tr>
                        <th>Hostname</th>
                        <th>{1}</th>
                    </tr>
                </tbody>
            </table>
            """.format(ip, hostname)

            plain_text_body += """\
            IP: {0}\nHostname: {1}\n\n
            """.format(ip, hostname)

            text, html = self.populate_vulns(vulns)
            plain_text_body += text
            html_body += html

        message_body = html_body if kwargs["get_html"] else plain_text_body
        if found_vulns:
            return True, message_body
        return True, "query resulted in no output"


    def populate_vulns(self, vulns):
        """
        helper function to iterate through vulnerablities found for IP to create message body
        :param vulns: result of sql query
        :return: (plain_text, html): plain_text and html versions of message body
        """
        plain_text_body = ""
        html_body = ""
        for i, v in enumerate(vulns):
            plain_text_body += "\n{0})  {1}\nSeverity: {2} \nSummary:{3} \n\nSolution:{4}\n\n".format(
                i + 1, v["NVT_Name"], v["Severity"], v["Summary"], v["Solution"])

            html_body += """ 
            <table style=" width: 650px; border-collapse: collapse;">
            <tbody>
                <tr>
                    <td style="border: 1px solid black;"><b>Vulnerability</b></td>
                    <td style="border: 1px solid black;"><b>{0}</b></td>
                </tr>
                <tr>
                    <td  style="border: 1px solid black;">Severity</td>
                    <td  style="border: 1px solid black;">{1}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid black; vertical-align: top;">Summary</td>
                    <td  style="border: 1px solid black;">{2} </td>
                </tr>
                <tr>
                    <td style="border: 1px solid black; vertical-align: top;">Solution</td>
                    <td  style="border: 1px solid black;">{3} </td>
                </tr>
            </tbody>
            </table>
            <p>&nbsp;</p>
            """.format(v["NVT_Name"], v["Severity"], v["Summary"], v["Solution"])
        return plain_text_body, html_body

    def create_csv_file(self, **kwargs):
        """
        method to create a csv file of vulnerability info and return a file path string to the created file
        :param kwargs: user_id (string/None): store vulnerabilities for a specific user, as_admin (bool) - store vulnerabilities
        intended for admins
        :return: (status (boolean), file path)
        """
        if kwargs["as_admin"]:
            query_res = self.query_for_vulnerabilities()
            filename = "admin_vulnerabilities.csv"
        else:
            query_res = self.query_for_vulnerabilities(user_id=kwargs["user_id"])
            filename = "{}_vulnerabilities.csv".format(self.conn.identity.find_user(kwargs["user_id"])["name"])

        file_path = kwargs["dir_path"]+filename
        if query_res:
            keys = query_res[0].keys()
            with open(file_path, "w") as output_file:
                writer = csv.DictWriter(output_file, keys)
                writer.writeheader()
                writer.writerows(query_res)

            return True, file_path
        return True, "query resulted in no output"
