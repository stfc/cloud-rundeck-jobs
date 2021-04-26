import json, datetime, sys
from MessageReceiver import MessageReceiver
import openstack, requests
from configparser import ConfigParser
CONFIG_FILE_PATH = "/etc/rabbitmq-utils/HypervisorConfig.ini"

class HostMessageReceiver(MessageReceiver):
    """ class to handle receiving and validating a message dealing with Hosts
    from a rabbitmq queue """
    def getHelperFunc(self, func_type):
        """Function to get Callback Function For Corresponding Message Types"""
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
        """ when message received is a REBOOT_HOST message """
        try:
            host_name = body["message"]["host_name"]
        except KeyError as e:
            return (False, "Malformed Message: {0}".format(repr(e)))

        host = self.conn.compute.find_hypervisor(host_name)
        if not host:
            return (False, "Hypervisor named {0} not found".format(host_name))

        service = self.conn.compute.find_service("nova-compute", host=host_name)
        if not service:
            return (False, "Service named {0} not found running on hypervisor {1}".format("nova-compute", host_name))

        if host["status"] == "enabled":
            print("disabling hypervisor")
            server_list = [server["name"] for server in self.conn.list_servers(all_projects=True) if server["hypervisor_hostname"] == host_name and server["status"] != "SHUTOFF"]
            if not server_list:
                self.conn.compute.disable_service(service, host_name, service["binary"], disabled_reason="disabled for reboot")
            else:
                return (False, "Servers {1} found on hypervisor {0} - aborting".format(server_list, host_name))

        print("scheduling downtime")
        start_time = datetime.datetime.now().timestamp() + 10
        end_time = start_time + 300
        if not self.scheduleDowntime(host_name, start_time, end_time):
            return (False, "Icinga downtime request failed - aborting")

        return (True, "Reboot Request Successful")

    def getHost(self, host, url):
        """ helper function to get hypervisor info from Icinga endpoint """
        r = requests.get(url, auth=(ICINGA_API_USERNAME, ICINGA_API_PASSWORD), verify=False,
         params = {"filter":"host.name==\"{}\"".format(host)})
        if r.status_code == requests.codes["ok"] and len(r.json()["results"]) > 0:
            return r.json()
        else:
            return None

    def scheduleDowntimeCallback(self, ch, method, properties, body):
        """Function to request downtime on icinga"""
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

        if not self.conn.compute.find_host(host_name):
            return (False, "Hypervisor not found")

        if not self.scheduleDowntime(host_name, start_time, end_time, author, comment,
        is_flexible, flexible_duration):
            return (False, "Icinga downtime request failed - aborting")

        return (True, "Downtime Scheduled for Host {0}".format(host_name))

    def scheduleDowntime(self, host, start_time, end_time, author="admin-vgc59244", comment="icinga schedule downtime test", is_flexible=False, flexible_duration=0):
        """Function to submit post request to shedule downtime on icinga"""
        if not self.getHost(host, ICINGA_HOSTS_ENDPOINT):
            return (False, "Host Called {0} Not Found in Icinga".format(host))

        if not end_time > start_time > datetime.datetime.now().timestamp():
            return(False, "Timestamps Given For Scheduling Downtime Are Malformed")

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
        """Function to remove downtime on icinga """
        try:
            host = body["message"]["host_name"]
        except KeyError as e:
            return (False, "Malformed Message: {0}".format(repr(e)))

        if not self.getHost(host, ICINGA_HOSTS_ENDPOINT):
            return (False, "Host Called {0} Not Found in Icinga".format(host))

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
        """Function to disable/enable service"""
        try:
            host_name = body["message"]["host_name"]
            service_binary = body["message"]["service_binary"]
            if body["metadata"]["message_type"] == "DISABLE_SERVICE":
                reason = body["message"]["reason"]
        except KeyError as e:
            return (False, "Malformed Message: {0}".format(repr(e)))

        host = self.conn.compute.find_hypervisor(host_name)
        if not host:
            return(False, "Host Called {0} not found".format(host_name))

        service = self.conn.compute.find_service(service_binary, host=host_name)
        if not service:
            return(False, "Service Called {0} not found on Host {1}".format(service_binary, host_name))

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
