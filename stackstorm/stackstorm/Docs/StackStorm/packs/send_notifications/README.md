# stackstorm-send-notifications-pack
A Stackstorm pack for sending notifications (emails), listening to and handling Rabbitmq messages.

# Emailing Configuration
Copy the example configuration in `stackstorm_send_notifications.yaml.example` to `/opt/stackstorm/configs/openstack.yaml` and edit as required

Note: When modifying the configuration in `/opt/stackstorm/configs/`, you will need to reload the new config file by running: `st2ctl reload --register-configs`

# Send Notification Workflows

`rabbit.execute.and.reply` - Workflow to execute a dynamic action and send the message via a RabbitMQ queue

Required Parameters:
- `action_inputs`: Object that stores inputs for the action that is to be run
- `dynamic_action`: Name of StackStorm Action to run

Optional Parameters:
- `host`: Rabbitmq hostname or IP address to connect to
  - default: `localhost`
- `port`: Rabbitmq TCP port to connect to
  - default: `5672`
- `username`: Rabbitmq username to connect with
  - default: `guest`
- `password`: Rabbitmq password to authenticate with
  - default: `guest`
- `exchange`: Rabbitmq exchange to publish the message on
  - default: `test_exchange`
- `exchange_type`: Rabbitmq exchange type to use
  - default: `direct`
- `exchange_durable`: Boolean to say whether or not the exchange is durable
  - default: true
- `routing_key`: The routing key for the message
  - default: `test_routing_key`


`rabbit.execute` - Workflow to execute a dynamic action

Required Parameters:
- `action_inputs`: Object that stores inputs for the action that is to be run
- `dynamic_action`: Name of StackStorm Action to run
Optional Parameters: None

# Send Notification Actions

`send.email` - Action to send an email.
  1. Allows sending as HTML or plaintext email, by setting flag `send_as_html`
  2. Must define a plaintext or html files for a standard header and footer for the email.
  3. The body of the email must be provided as a string
  4. Must provide the smtp_account name to use - defined in the config file

Required Parameters:
`body`: String of email body - either as plaintext or html
`subject`: String of email subject
`email_to`: Array of recipient email addresses
`email_from`: String for sender email address
  - (sending via a VM allows you to define the sender email address)

`header`: filepath to standard header file
`footer`: filepath to standard footer file

Optional Parameters:
`send_as_html`: Boolean, if true, send email as html, if false, as plaintext
  - default: true

`admin_override`: Boolean, if true override sending email, instead sending to a test email address.
  - default: true  # should be changed in production

`admin_override_email`: Email to send if `admin_override` set to true
  - default: jacob.ward@stfc.ac.uk

`smtp_account`: smtp account name to use - must be configured in email.yaml

`email_cc`: Array of email addresses to cc in
  - default (None) - not required

`attachment_filepaths`: Array of filepaths for file attache=4ments
  - default (None) - not required

# Rabbit Sensor

This pack contains a sensor called `RabbitSensor`
`RabbitSensor` is a passive sensor which listens for incoming Rabbitmq messages
  - once a message is received, it is parsed.
  - if the message is formatted correctly the sensor will dispatch a trigger:
    1. contains `metadata` and `message` fields
    2. contains a `message_type` parameter in `metadata` field

  - the trigger type dispatched is either:
    - `rabbit.reply.message`: if the message requires a reply. The `metadata` field must contain `reply_required: True`
    - `rabbit.message`: if message does not require a reply. The `metadata` field contains
    `reply_required: False`

These triggers are picked up by other rules in StackStorm (see Openstack Pack for examples)
An example rule is provided in this pack for testing - `rabbitmq.echo.rule`.

`rabbitmq.echo.rule` is a simple rule which matches if the `message_type` parameter for a rabbitmq message matches `TEST_ECHO`. If matched, the rule will call the `rabbit.execute.and.reply` action - which will echo the `message` parameter back on a given rabbitmq

# Future work

# TODO - formalise and test the process of replying via the rabbitmq queue
# TODO - allow sensor to read from multiple queues
