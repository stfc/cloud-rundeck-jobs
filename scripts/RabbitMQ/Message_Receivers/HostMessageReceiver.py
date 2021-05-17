import json, datetime, sys
from MessageReceiver import MessageReceiver
import openstack, requests
from configparser import ConfigParser
CONFIG_FILE_PATH = "/etc/rabbitmq-utils/HypervisorConfig.ini"

class HostMessageReceiver(MessageReceiver):
    """
    class to handle receiving and validating a message dealing with Hosts
    from a rabbitmq queue. Inherits from MessageReceiver base class

    Attributes
    ----------
    None

    Methods
    --------
    getHelperFunc(func_type):
        Overrides MessageReceiver getHelperFunc - determines how to handle a
        message, based on its message type. Calls appropriate helper function

    hostRebootCallback(ch, method, properties, body):
        Helper function to handle any Reboot Hypervisor Message
        returns (Bool, String) tuple after handling message

    getHost(host, url):
        Helper function to get hypervisor from Icinga
        returns (Json Object) Icinga information regarding hypervisor or None

    scheduleDowntimeCallback(ch, method, properties, body):
        Helper function to handle scheduling downtime for a Hypervisor
        returns (Bool, String) tuple after handling message

    scheduleDowntime(host, start_time, end_time, author="admin-vgc59244", comment="icinga schedule downtime test", is_flexible=False, flexible_duration=0):
        Helper function called by scheduleDowntimeCallback to make a Python
        request to Icinga to schedule Hypervisor Downtime
        returns (Bool, String) tuple after handling message

    removeDowntimeCallback(ch, method, properties, body)
        Helper function to handle removing all downtimes placed on a Hypervisor
        returns (Bool, String) tuple after handling message

    serviceCallback(ch, method, properties, body, service_func)
        Helper function to handle status change for a service running on Hypervisor
        returns (Bool, String) tuple after handling message
    """
    def getHelperFunc(self, func_type):
        """
        Function to get Callback Function For Corresponding Message Types
            Parameters:
                func_type (string) : unique message type identifier
            Returns:
                (lambda function()) which needs to be called to handle
                that particular message
        """
        return {
            "REBOOT_HOST":      self.hostRebootCallback,
            "SCHEDULE_DOWNTIME":self.scheduleDowntimeCallback,
            "REMOVE_DOWNTIME":  self.removeDowntimeCallback,

            "DISABLE_SERVICE":  lambda ch, method, properties, body:
            self.serviceCallback(ch, method, properties, body, self.conn.compute.disable_service),

            "ENABLE_SERVICE":   lambda ch, method, properties, body:
            self.serviceCallback(ch, method, properties, body, self.conn.compute.enable_service),
        }.get(func_type, None)

    def hostRebootCallback(self, ch, method, properties, body):
        """
        Function called when message has REBOOT_HOST message type
            Parameters:
                ch : rabbitmq channel information
                method : rabbitmq delivery method information
                properties: rabbitmq message properties
                body: message payload
            Returns: (Bool, String): tuple after handling message - if handling
            succeeded/failed (Bool) and return message/reason failed (String)
        """
        # validate message payload:
        # message contains valid hypervisor
        try:
            host_name = body["message"]["host_name"]
        except KeyError as e:
            return (False, "Malformed Message: {0}".format(repr(e)))
        host = self.conn.compute.find_hypervisor(host_name)
        if not host:
            return (False, "Hypervisor named {0} not found".format(host_name))
        # if hypervisor contains valid "nova-compute" service on the hypervisor
        # must disable services on hypervisor
        # TODO: check which services need to be disabled - currently only checking nova-compute service
        service = self.conn.compute.find_service("nova-compute", host=host_name)
        if service:
            # disable "nova-compute" service if not already disabled
            if host["status"] == "enabled":
                print("disabling hypervisor")
                server_list = [server["name"] for server in self.conn.list_servers(all_projects=True) if server["hypervisor_hostname"] == host_name and server["status"] != "SHUTOFF"]
                if not server_list:
                    self.conn.compute.disable_service(service, host_name, service["binary"], disabled_reason="disabled for reboot")
                else:
                    return (False, "Servers {1} found on hypervisor {0} - aborting".format(server_list, host_name))
        # schedule downtime
        print("scheduling downtime")
        start_time = datetime.datetime.now().timestamp() + 10
        end_time = start_time + 300
        if not self.scheduleDowntime(host_name, start_time, end_time):
            return (False, "Icinga downtime request failed - aborting")
        return (True, "Reboot Request Successful")

    def getHost(self, host, url):
        """
        Helper function to submit GET request to Icinga endpoin to get hypervisor info
            Parameters:
                host (String): the host/hypervisor name
                url (String): Icinga endpoint URL to query with GET request
            Returns: Json object of information found or None if not found
        """
        r = requests.get(url, auth=(ICINGA_API_USERNAME, ICINGA_API_PASSWORD), verify=False,
         params = {"filter":"host.name==\"{}\"".format(host)})
        if r.status_code == requests.codes["ok"] and len(r.json()["results"]) > 0:
            return r.json()
        else:
            return None

    def scheduleDowntimeCallback(self, ch, method, properties, body):
        """
        Function called when message has SCHEDULE_DOWNTIME message type
            Parameters:
                ch : rabbitmq channel information
                method : rabbitmq delivery method information
                properties: rabbitmq message properties
                body: message payload
            Returns: (Bool, String): tuple after handling message - if handling
            succeeded/failed (Bool) and return message/reason failed (String)
        """
        # validate message
        try:
            host_name = body["message"]["host_name"]
            start_time = body["message"]["start_time"]
            end_time = body["message"]["end_time"]
            author = body["message"]["author"]
            comment =  body["message"]["comment"]
            is_flexible = body["message"]["is_flexible"]
            flexible_duration = body["message"]["flexible_duration"]
        except KeyError as e:
            return (False, "Malformed Message: {0}".format(repr(e)))
        # check if hypervisor exists
        if not self.conn.compute.find_hypervisor(host_name):
            return (False, "Hypervisor not found")

        # schedule downtime on Icinga
        return self.scheduleDowntime(host_name, start_time, end_time, author, comment,
        is_flexible, flexible_duration)

    def scheduleDowntime(self, host, start_time, end_time, author="admin-vgc59244", comment="icinga schedule downtime test", is_flexible=False, flexible_duration=0):
        """
        Function to submit post request to shedule downtime on icinga
            Parameters:
                host (string): name of host/hypervisor,
                start_time (int): Unix timestamp - time when downtime scheduled to start
                end_time (int): Unix timestamp - time when downtime scheduled to end
                author (string) Default ("admin-vgc59244"): author/name of user who scheduled downtime
                comment (string) Default ("icinga schedule downtime test"): reason/comment for downtime
                is_flexible (bool) Default (false): if downtime is flexible - can restart before end_time ends
                flexible_duration (int): time in seconds - how long the flexible duration lasts
            Returns:
                (Bool, String): tuple after handling message - if handling
                succeeded/failed (Bool) and return message/reason failed (String)
        """
        # check if hypervisor exists in Icinga
        if not self.getHost(host, ICINGA_HOSTS_ENDPOINT):
            return (False, "Host Called {0} Not Found in Icinga".format(host))
        # check the timestamps are valid
        if not end_time > start_time > datetime.datetime.now().timestamp():
            return(False, "Timestamps Given For Scheduling Downtime Are Malformed")
        # make python request
        # TODO: Schedule downtime for all services or a few?
        # all_services=1 - schedule downtime for all services

        r = requests.post(ICINGA_SCHEDULE_DOWNTIMES_ENDPOINT,
            headers={"Accept":"application/json"},
            auth=(ICINGA_API_USERNAME, ICINGA_API_PASSWORD),
            verify=False,
            data=json.dumps({
                "type":"Host",
                "filter": "host.name==\"{}\"".format(host),
                "author": author,
                "start_time": start_time,
                "end_time": end_time,
                "comment": comment,
                "all_services":1,
                "duration": flexible_duration if is_flexible else (end_time - start_time),
                "fixed": False if is_flexible else True
            }))
        if r.status_code == requests.codes["ok"]:
            return(True, "Downtime of Host {0} Scheduled For {1} Until {2} (Fixed: {3}, Duration: {4})".format(
                host,
                datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d, %H:%M:%S'),
                datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d, %H:%M:%S'),
                not is_flexible,
                flexible_duration if is_flexible else (end_time - start_time)
            ))
        else:
            return(False, "Downtime Could Not Be Scheduled: {0}".format(r.text))

    def removeDowntimeCallback(self, ch, method, properties, body):
        """
        Function called when message has REMOVE_DOWNTIME message type
            Parameters:
                ch : rabbitmq channel information
                method : rabbitmq delivery method information
                properties: rabbitmq message properties
                body: message payload
            Returns: (Bool, String): tuple after handling message - if handling
            succeeded/failed (Bool) and return message/reason failed (String)
        """
        # validate host_name
        try:
            host = body["message"]["host_name"]
        except KeyError as e:
            return (False, "Malformed Message: {0}".format(repr(e)))

        # check if hypervisor exists in Icinga
        if not self.getHost(host, ICINGA_HOSTS_ENDPOINT):
            return (False, "Host Called {0} Not Found in Icinga".format(host))

        # remove downtime
        # TODO: Make more specific removal possible - based on downtime id
        r = requests.post(ICINGA_REMOVE_DOWNTIMES_ENDPOINT,
                          headers={"Accept":"application/json"},
                          auth=(ICINGA_API_USERNAME, ICINGA_API_PASSWORD),
                          verify=False,
                          data=json.dumps({
                              "type": "Host",
                              "filter":"host.name==\"{}\"".format(host)
                          })
                         )
        if r.status_code == requests.codes["ok"]:
            return(True, "Downtimes of Host {0} Removed".format(host))
        else:
            return(False, "Downtimes Could Not Be Removed: {0}".format(r.text))

    def serviceCallback(self, ch, method, properties, body, service_func):
        """
        Function called when message involves changing the state of a
        service on a hypervisor
            Parameters:
                ch : rabbitmq channel information
                method : rabbitmq delivery method information
                properties: rabbitmq message properties
                body: message payload
                service_func: specific service status change message type
            Returns: (Bool, String): tuple after handling message - if handling
            succeeded/failed (Bool) and return message/reason failed (String)
        """
        # validate payload
        try:
            host_name = body["message"]["host_name"]
            service_binary = body["message"]["service_binary"]
            if body["metadata"]["message_type"] == "DISABLE_SERVICE":
                reason = body["message"]["reason"]
        except KeyError as e:
            return (False, "Malformed Message: {0}".format(repr(e)))

        # check if hypervisor exists
        host = self.conn.compute.find_hypervisor(host_name)
        if not host:
            return(False, "Host Called {0} not found".format(host_name))

        # check if service exists on hypervisor
        service = self.conn.compute.find_service(service_binary, host=host_name)
        if not service:
            return(False, "Service Called {0} not found on Host {1}".format(service_binary, host_name))
        # perform service status change (ENABLE_SERVICE or DISABLE_SERVICE)
        try:
            if body["metadata"]["message_type"] == "DISABLE_SERVICE":
                service_func(service, host_name, service_binary, reason)
            else:
                service_func(service, host_name, service_binary)
            return (True, "Service Status Changed")
        except Exception as e:
            return (False, "Service Status Could Not Be Changed: {0}".format(repr(e)))

if __name__ == "__main__":
    try:
        configparser = ConfigParser()
        configparser.read(CONFIG_FILE_PATH)

        RABBIT_PORT = configparser.get("global", "RABBIT_PORT")
        RABBIT_HOST = configparser.get("global", "RABBIT_HOST")
        QUEUE = configparser.get("global", "QUEUE")
        EXCHANGE_TYPE = configparser.get("global", "EXCHANGE_TYPE")

        ICINGA_API_USERNAME = configparser.get("icinga", "ICINGA_API_USERNAME")
        ICINGA_API_PASSWORD = configparser.get("icinga", "ICINGA_API_PASSWORD")
        ICINGA_URL = configparser.get("icinga", "ICINGA_URL")

        ICINGA_HOSTS_ENDPOINT = configparser.get("icinga", "ICINGA_HOSTS_ENDPOINT")
        ICINGA_DOWNTIMES_ENDPOINT = configparser.get("icinga", "ICINGA_DOWNTIMES_ENDPOINT")
        ICINGA_SCHEDULE_DOWNTIMES_ENDPOINT = configparser.get("icinga", "ICINGA_SCHEDULE_DOWNTIMES_ENDPOINT")
        ICINGA_REMOVE_DOWNTIMES_ENDPOINT = configparser.get("icinga", "ICINGA_REMOVE_DOWNTIMES_ENDPOINT")

        ROUTING_KEY = configparser.get("hostmessageconfig", "ROUTING_KEY")

        CLOUD_NAME = configparser.get("openstack", "CLOUD_NAME")
        REGION = configparser.get("openstack", "REGION")
    except Exception as e:
        print("error - unable to read config file")
        print(repr(e))
        sys.exit(1)
    try:
        conn = openstack.connect(cloud=CLOUD_NAME, region_name=REGION)
    except Exception as e:
        print("could not establish openstack connection")
        print(repr(e))
        sys.exit(1)
    try:
        receiver = HostMessageReceiver(conn, RABBIT_HOST, RABBIT_PORT, QUEUE, EXCHANGE_TYPE, ROUTING_KEY)
    except KeyboardInterrupt:
        print("Interrupted")
