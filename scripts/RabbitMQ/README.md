# RabbitMQ Scripts
A set of python scripts that allow messages to be sent and received from a RabbitMQ
server. Each message consists of a set of arguments and a message_type that will
manipulate an openstack compute resource in some way. I.e. scheduling hypervisor downtime by setting message_type as SCHEDULE_DOWNTIME.

Currently split into message receiver and client scripts

  - client scripts send messages to a queue hosted by a RabbitMQ server

  - message receiver scripts listen into that queue and handle each request made

# Message Receiver
MessageReceiver - base class to handle receiving generic messages from RabbitMQ

ServerMessageReceiver - reads queue for messages that manipulate openstack
servers. Inherits from MessageReceiver
  - such as change statuses, create or delete servers

HostMessageReceiver - reads queue for messages that manipulate openstack
hypervisors. Inherits from MessageReceiver
  - such as scheduling downtimes, disabling/enabling services on the hypervisor

# Client (Message Senders)
HypervisorReboot - a script that runs on a hypervisor, sends REBOOT_HOST message
to RabbitMQ server if the hypervisor requires a reboot. Disables services and
handles scheduling downtimes

HypervisorWakeup - a script that runs when a hypervisor upon startup, cancelling
any Icinga downtimes and enabling compute service on them.

RecoverVM - a script that reboots/deletes/shuts down a set of given servers.

# Utilities
MessageCreator - python class that creates a message given a message_type and
a set of arguments.
