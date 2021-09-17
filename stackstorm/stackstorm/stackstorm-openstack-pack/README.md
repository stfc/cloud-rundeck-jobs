# stackstorm-openstack-pack
A Stackstorm pack for running Openstack scripts:
1. Handle creating Internal and External Projects in Openstack
2. Automatically list VM properties per user based on certain criteria
  - shutoff/error status, older/younger than threshold etc.
3. Create/Delete VMs
4. Reboot Hypervisors, schedule downtimes
5. Stop/Restart/Reboot VMs
6. Run miscellaneous Openstack Commands

# Setup Openstack

Openstack openrc config file is required in order to run Openstack Commands.
The openrc file must be stored in `etc/openstack/clouds.yaml` or `/home/<user>/.config/openstack/clouds.yaml`.

# Openstack Workflow

`project.create.internal` - Action Orquesta workflow to create a pre-configured Openstack Project to be used internally
1. Create Project
2. Then, run the following actions in parallel:
  - Create security groups default, http and https
  - Populate admin and stfc user list for project
  - create default rbac policy
3. Then, configure security group rules for default, http and https after the respective security group is created

Required Parameters:
- `project_name`: Name of the project
- `project_description`: Description of the project
- `admin_user_list`: Array of users who must have admin access to the project
- `stfc_user_list`: Array of STFC users with access to the project

Optional Parameters:
- `network_name`: Network to create project on
  - default: Internal
- `default_network_internal_rules`: JSON of default network rules
  - default: (Taken from Datastore and decrypted)
- `http_network_internal_rules`: JSON of http network rules
  - default: (Taken from Datastore and decrypted)
- `https_network_internal_rules`: JSON of https network rules
  - default: (Taken from Datastore and decrypted)

`project.create.external` - Action Orquesta workflow to create a pre-configured Openstack project to be made available externally
1. Create Project
2. Then, run the following actions in parallel:
  - Create security group default
  - Create external Network
  - Set the quota for the project
  - Populate admin and stfc user list for project
3. Once quota assigned, setup default external security rules
4. Once external network created:
  - Create RBAC policy
  - Create and configure Router and Subnet
  - Assign float ips

Required Parameters:
- `project_name`: Name of the project
- `project_description`: Description of the project
- `network_name`: Name of network for project
- `network_description`: Description of network for project
- `subnet_name`: Name of subnet for project
- `subnet_description`: Description of subnet for project
- `router_name`: Name of router for project
- `router_description`: Description of router for project
- `ip_number`: Number of ips to assign to project
- `admin_user_list`: Array of users who must have admin access to the project
- `stfc_user_list`: Array of STFC users with access to the project

Optional Parameters:
- `default_network_external_rules`: JSON of default network rules
  - default: (Taken from Datastore and decrypted)
- `egress_external_ips`: Array of IPs to be given TCP/UDP egress rules
  - default: (Taken from Datastore and decrypted)

`send.server.email` - Action Orquesta workflow to email users information about their servers (Shutoff/Error VM Reminders)
  1. Perform a search on servers per user
  2. Email each user the results of the search of servers that correspond to them

Required Parameters:
- `query_preset`: Name of preset query - i.e. server_shutoff etc

Optional Parameters:
`properties_to_select`: Properties to select for servers
  - default: `["server_id", "server_name", "server_status", "user_name", "user_email"]`
`search_criteria`: Array of additional properties to select for:
  - default: `None` - not required
  provide in format: `[<criteria_name>, [<ARGS>]]`
`sort_by_criteria`: Property selected to sort results by
  - default: `None` - not required
`subject`: String of email subject
  - default: `Test Message`
`email_from`: String for sender email address
  - default: `cloud-support@gridpp.rl.ac.uk`
`header`: filepath to standard header file
  - default: `/home/<user>/html_templates/header.html`
`footer`: filepath to standard footer file
  - default: `/home/<user>/html_templates/footer.html`
`send_as_html`: Boolean, if true, send email as html, if false, as plaintext
  - default: `true`
`admin_override`: Boolean, if true override sending email, instead sending to a test email address.
  - default: `true`  # should be changed in production
`admin_override_email`: Email to send if `admin_override` set to true
  - default: `jacob.ward@stfc.ac.uk`
`smtp_account`: smtp account name to use - must be configured in email.yaml
  - default: `default`
`email_cc`: Array of email addresses to cc in
  - default: `None` - not required
`attachment_filepaths`: Array of filepaths for file attache=ments
  - default: `None` - not required

# Actions
Contains the following actions:
Generally, Stackstorm openstack actions are written to be very similar and easy to understand for anyone who has used Openstack CMD commands
  - generally each openstack resource `server, hypervisor, float.ip, etc` have 4 basic commands `create`, `delete`, `update`, `show`
    - NOTE: CURRENTLY MANY OF THESE METHODS - (ESPECIALLY CREATE AND DELETE) ARE NOT IMPLEMENTED, (AND MAY NOT BE IF THEY ARE NOT FEASIBLE/POSSIBLE UNDER CURRENT CONSTRAINTS IMPOSED BY THE CLOUD OPS TEAM)
    - they may also have other commands specific to them. `i.e. server.reboot, server.restart etc`

## Openstack List Actions

In addition, `hypervisor, server, user, float.ip and project` all have `list` actions:
  - allows for more refined and complex searches than what openstack currently allows
  - uses the `queryopenstack` library: see usage here: <link to queryopestack git>


## Reboot/Disable Hypervisor Actions

`hypervisor.remove.icinga.downtime`: Removes all downtimes associated with a hypervisor

  Required Parameters:
    `hypervisor`: Name or ID of hypervisor to remove downtimes for in Icinga

`hypervisor.schedule.icinga.downtime`: schedules downtime for `nova-compute` service on hypervisor

  Required Parameters:
    `hypervisor`: Name or ID of hypervisor to schedule downtimes for in Icinga
    `start_time_unix`: Unix timestamp for start of downtime (ignored if timestamp string is given)
    `end_time_unix`: Unix timestamp for end of downtime (ignored if timestamp string is given)

  Optional Parameters:
    `start_time_str`: timestamp in format `YYYY-MM-DD, HH:MM:SS` for start of downtime
      - default: `None` - not required
    `end_time_str`: timestamp in format `YYYY-MM-DD, HH:MM:SS` for end of downtime
      - default: `None` - not required
    `author`: `who scheduled the downtime`
      - default: StackStorm
    `comment`: `reason for scheduling downtime`
      - default: Scheduled using Stackstorm - reason not given
    `is_flexible`: if icinga downtime is flexible
      - default: `false`
    `flexible_duration`: if flexible downtime, duration in seconds
      - default: 0

`hypervisor.service.disable`: disables hypervisor service in openstack
- `nova-compute` is name of service for VMs, if given as `service_binary`, action only succeeds only if no servers currently being hosted by hypervisor
- TODO: Automated live migrations?

  Required Parameters:
    `hypervisor`: Name or ID of hypervisor to disable a service on
    `service_binary`: Name of service to disable

  Optional Parameters:
    `reason`: Reason to disable service


`hypervisor.service.enable`: enables hypervisor service in openstack
  Required Parameters:
    `hypervisor`: Name or ID of hypervisor to enable a service on
    `service_binary`: Name of service to enable

`hypervisor.reboot`:
action that:
  1. Disables hypervisor (same process as hypervisor disable)
  2. Schedules downtime on icinga
TODO: convert to orquesta workflow

# Rules
A number of rules are provided in this pack on a number of triggers defined in the `stackstorm_send_notifications` pack to handle rabbitmq message commands.

## Hypervisor Rules

`rabbitmq.hypervisor.disable.service.rule`
  - matches trigger `rabbit.message` with `message_type=HYPERVISOR_DISABLE_SERVICE` and calls `hypervisor.service.disable` using `stackstorm_send_notification.rabbit.execute`

`rabbitmq.hypervisor.enable.service.rule`
- matches trigger `rabbit.message` with `message_type=HYPERVISOR_ENABLE_SERVICE` and calls `hypervisor.service.enable` using `stackstorm_send_notification.rabbit.execute`

`rabbitmq.hypervisor.reboot.rule`
- matches trigger `rabbit.reply.message` with `message_type=HYPERVISOR_REBOOT` and calls `hypervisor.reboot` using `stackstorm_send_notification.rabbit.execute.and.reply`

`rabbitmq.hypervisor.schedule.icinga.downtime.rule`
- matches trigger `rabbit.message` with `message_type=HYPERVISOR_SCHEDULE_ICINGA_DOWNTIME` and calls `hypervisor.schedule.icinga.downtime` using `stackstorm_send_notification.rabbit.execute`

`rabbitmq.hypervisor.remove.icinga.downtime.rule`
- matches trigger `rabbit.message` with `message_type=HYPERVISOR_REMOVE_ICINGA_DOWNTIME` and calls `hypervisor.remove.icinga.downtime` using `stackstorm_send_notification.rabbit.execute`

## Server Rules

`rabbitmq.server.create.rule`
- matches trigger `rabbit.message` with `message_type=CREATE_VM` and calls `server.create` using `stackstorm_send_notification.rabbit.execute`

`rabbitmq.server.delete.rule`
- matches trigger `rabbit.message` with `message_type=DELETE_VM` and calls `server.delete` using `stackstorm_send_notification.rabbit.execute`

`rabbitmq.server.reboot.rule`
- matches trigger `rabbit.message` with `message_type=REBOOT_VM` and calls `server.reboot` using `stackstorm_send_notification.rabbit.execute`
# NOTE: May need to change this to a execute and reply version - depending on use case?

`rabbitmq.server.shutdown.rule`
- matches trigger `rabbit.message` with `message_type=SHUTDOWN_VM` and calls `server.shutdown` using `stackstorm_send_notification.rabbit.execute`

`rabbitmq.server.restart.rule`
- matches trigger `rabbit.message` with `message_type=RESTART_VM` and calls `server.restart` using `stackstorm_send_notification.rabbit.execute`


# Aliases and Chatops
A number of Aliases are pre-configured to allow listing of information using ChatOps.
Aliases are a more human-readable method of invoking these actions.

ChatOps requires Aliases to be defined for any Actions that ChatOps is allowed to invoke
  - to define how bot reads, acknowledges, and responds to commands run via Slack

Currently Aliases have been written for `list` actions for `float.ip, hypervisor, project, server and user`
  - NOTE: currently `user` list option can only give information on admin users (not stfc domain users) - it is not possible to list stfc users using `queryopenstack` library
  - NOTE: currently, it takes 10mins to display server information

An example of a list command is:

`!hypervisor list properties host_id, host_name, host_status preset host_disabled`   

This command will list hypervisor ids, names and statuses for all disabled hypervisors

The command is explained below:
  - `!hypervisor list` - run action `hypervisor.list`
  - `properties host_id, host_name, host_status` - pass array [`host_id`, `host_name`, `host_status`] as `properties_to_select`
 - `preset host_disabled` - use preset `host_disabled` to search

NOTE: currently Slack will only output results up to the maximum characters allowed for one post. Look into providing a csv/txt file output attachment instead.

# Misc

Other examples of atomic Actions are shown below (not an exhaustive list):
`floating.ip.create` - Action to assign a number of floating IP to a project
`network.create` - Action to create a network for a project
`network.rbac.create` - Action to create Role Based Access Control rules on a network
`project.create` - Action to create a new openstack project (not-configured)
`project.show` - Action to find and list an Openstack Project's properties given it's Name or ID
`quota.set` - Action to set project quota
`role.add` - Action to add user role to a project
`router.add.interface` - Action to add interface to a router
`router.create` - Action to create a Openstack router
`security.group.create` - Action to create new security group for a project
`security.group.list` - Action to list security groups and their properties for a given project
`security.group.rule.create` - Action to create a new rule for a given security
group
`server.list` - Action to list server properties given some criteria
`subnet.create` - Action to create an Openstack subnet
`user.get.email` - Action to get a user's email address given their Name/ID

The Following are Orquesta workflows - which chain together a number of scripts:
