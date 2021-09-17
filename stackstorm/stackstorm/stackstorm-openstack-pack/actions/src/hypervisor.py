"""TODO:
hypervisor show
hypervisor reboot
hypervisor schedule downtime
hypervisor remove downtime
hypervisor service enable
hypervisor service disable
"""
import datetime
import requests
import json
from openstack_action import OpenstackAction

class Hypervisor(OpenstackAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.func = {
            "hypervisor_reboot": self.hypervisor_reboot,
            "hypervisor_schedule_icinga_downtime": self.schedule_icinga_downtime,
            "hypervisor_remove_icinga_downtime": self.remove_icinga_downtime,
            "hypervisor_service_enable": lambda **kwargs: self.hypervisor_service_status(func="enable", **kwargs),
            "hypervisor_service_disable": lambda **kwargs: self.hypervisor_service_status(func="disable", **kwargs),
            "hypervisor_show": self.hypervisor_show
            # hypervisor create
            # hypervisor update
            # hypervisor get stats
        }

    def hypervisor_show(self, hypervisor):
        """
        Show Hypervisor information
        :param hypervisor (String): Hypervisor Name or ID
        :return: (status (Bool), reason/output (String/Dict))
        """
        try:
            hypervisor = self.conn.compute.find_hypervisor(hypervisor, ignore_missing=False)
        except Exception as e:
            return False, "IP not found {}".format(repr(e))
        return True, hypervisor

    def hypervisor_reboot(self, hypervisor, author, comment):
        """
        Reboot Hypervisor
        :param hypervisor (String): Hypervisor Name or ID
        :param author (String): Name of person authorising the reboot
        :param comment (String): Reason for reboot
        :return: (status (Bool), reason/output (String))
        """
        hypervisor_id = self.find_resource_id(hypervisor, self.conn.compute.find_hypervisor)
        if not hypervisor_id:
            return False, "No Hypervisor found with Name or ID {}".format(hypervisor)

        try:
            hypervisor = self.conn.compute.find_hypervisor(hypervisor_id, ignore_missing=False)
            host_name = hypervisor["hypervisor_hostname"]
            if not hypervisor:
                return False, "Malformed Message: Hypervisor with name {0} not found".format(host_name)
        except Exception as e:
            return False, "Error finding hypervisor {}".format(e)

        service = self.conn.compute.find_service("nova-compute", host=host_name)
        if service:
            if hypervisor["status"] == "enabled":
                server_list = [server["name"] for server in
                               self.conn.list_servers(filters={"all_tenants": True, "host": host_name, "limit": 10000})]
                if not server_list:
                    self.conn.compute.disable_service(service, host_name, service["binary"],
                                                      disabled_reason="disabled for reboot")
                else:
                    return False, "Servers {0} found active on Hypervisor {1} - aborting".format(server_list, host_name)

        start_time = datetime.datetime.now().timestamp() + 10
        end_time = start_time + 300

        if not self.schedule_icinga_downtime(host_name, start_time_unix=start_time, end_time_unix=end_time,
                                             start_time_str=None, end_time_str=None, author=author, comment=comment,
                                             is_flexible=False, flexible_duration=0):

            return False, "Icinga downtime request failed - aborting"
        return True, "Reboot Request Successful"

    def schedule_icinga_downtime(self, hypervisor, start_time_unix, end_time_unix, start_time_str, end_time_str,
                                 author, comment, is_flexible, flexible_duration):
        """
            Function to submit post request to schedule downtime on Icinga
                :param hypervisor: (String): Hypervisor Name or ID
                :param start_time_unix (Unix timestamp): time when downtime scheduled to start (used by default)
                :param end_time_unix (Unix timestamp): time when downtime scheduled to end (used by default)
                :param start_time_str (String): time when downtime scheduled to start format:'%Y-%m-%d, %H:%M:%S'
                :param end_time_str (String): time when downtime scheduled to end format:'%Y-%m-%d, %H:%M:%S'
                :param author: (String): author/name of user who scheduled downtime
                :param comment: (String): reason/comment for downtime
                :param is_flexible: (Bool): set if downtime is flexible
                :param flexible_duration: (Int): time in seconds, how long the flexible duration lasts
                :return (status (Bool), reason/output (String))
        """

        hypervisor_id = self.find_resource_id(hypervisor, self.conn.compute.find_hypervisor)
        if not hypervisor_id:
            return False, "No Hypervisor found with Name or ID {}".format(hypervisor)

        host_name = self.conn.compute.find_hypervisor(hypervisor_id)["hypervisor_hostname"]
        if not self.get_host_from_icinga(host_name):
            return False, "Host called {0} not found in Icinga".format(host_name)

        start_time = start_time_unix
        if start_time_str:
            start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d, %H:%M:%S').timestamp()
            # convert to unix timestamp

        end_time = end_time_unix
        if end_time_str:
            start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%d, %H:%M:%S').timestamp()
            # convert to unix timestamp

        if start_time == "" or end_time == "":
            return False, "No end_time or start_time values given"

        if not end_time > start_time > datetime.datetime.now().timestamp():
            return False, "Timestamps given for scheduling downtime are malformed - string needs to be YYYY-MM-DD, HH-MM-SS"

        r = requests.post(self.config.get("icinga_schedule_downtime_endpoint", None),
                          headers={"Accept": "application/json"},
                          auth=(self.config.get("icinga_username"), self.config.get("icinga_password")),
                          verify=False,
                          data=json.dumps({
                              "type": "Host",
                              "filter": "host.name==\"{}\"".format(host_name),
                              "author": author,
                              "start_time": start_time,
                              "end_time": end_time,
                              "comment": comment,
                              "all_services": 1,
                              "duration": flexible_duration if is_flexible else (end_time - start_time),
                              "fixed": False if is_flexible else True
                          }))

        if r.status_code == requests.code["ok"]:
            return True, "Downtime of Host {0} Scheduled For {1} Until {2} (Fixed: {3}, Duration: {4})".format(
                host_name,
                datetime.datetime.fromtimestamp(start_time).strftime('%Y-%m-%d, %H:%M:%S'),
                datetime.datetime.fromtimestamp(end_time).strftime('%Y-%m-%d, %H:%M:%S'),
                not is_flexible,
                flexible_duration if is_flexible else (end_time - start_time)
            )
        else:
            return False, "Downtime could not be scheduled: {0}".format(r.text)

    def remove_icinga_downtime(self, hypervisor):
        """
        Function called when message has REMOVE_DOWNTIME message type
            :param hypervisor (String): Hypervisor Name or ID
            :return (status (Bool), reason/output (String))
        """
        hypervisor_id = self.find_resource_id(hypervisor, self.conn.compute.find_hypervisor)
        if not hypervisor_id:
            return False, "No Hypervisor found with Name or ID {}".format(hypervisor)
        hypervisor_hostname = self.conn.compute.find_hypervisor(hypervisor_id, ignore_missing=False)["hypervisor_hostname"]

        if not self.get_host_from_icinga(hypervisor_hostname):
            return False, "Host called {0} not found in Icinga".format(hypervisor_hostname)

        r = requests.post(self.config.get("icinga_remove_downtimes_endpoint", None),
                          headers={"Accept":"application/json"},
                          auth=(self.config.get("icinga_username"), self.config.get("icinga_password")),
                          verify=False,
                          data=json.dumps({
                              "type": "Host",
                              "filter": "host.name==\"{}\"".format(hypervisor_hostname)
                          }))
        if r.status_code == requests.codes["ok"]:
            return True, "Downtimes of Host {0} Removed".format(hypervisor_hostname)
        else:
            return False, "Downtimes could not be removed: {0}".format(r.text)

    def hypervisor_service_status(self, func, hypervisor, service_binary, **kwargs):
        """
        Function called when message involves changing the state of a service on a hypervisor
            :param func: service status change message type
            :param host_name (String): Name of hypervisor to change status for
            :param service_binary (String): Name of service on hypervisor to change status for
            :param kwargs: Misc properties/arguments
            :return (status (Bool), reason/output (String))
        """
        hypervisor_id = self.find_resource_id(hypervisor, self.conn.compute.find_hypervisor)
        if not hypervisor_id:
            return False, "No Hypervisor found with Name or ID {}".format(hypervisor)
        host_name = self.conn.compute.find_hypervisor(hypervisor_id, ignore_missing=False)["hypervisor_hostname"]
        service = self.conn.compute.find_service(service_binary, host=host_name)
        if not service:
            return False, "Service called {0} not found on host {1}".format(service_binary, host_name)
        service_func = {
            "disable": lambda service, host_name, service_binary: self.conn.compute.disable_service(service, host_name,
                                                                                                    service_binary,
                                                                                                    kwargs["reason"]),
            "enable": self.conn.compute.enable_service
        }.get(func, None)
        try:
            service_func(service, host_name, service_binary)
        except Exception as e:
            return False, "Service status could not be changed: {0}".format(repr(e))
