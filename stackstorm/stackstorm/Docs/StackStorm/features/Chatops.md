# ChatOps With StackStorm

## ChatOps Basics

ChatOps provides a way to collaborate within teams. ChatOps supports a methodology known as conversation-driven development.

ChatOps exposes commands in a company chat room like Slack, allowing operational or developmental workflows to be run using ChatBots

The goal of ChatOps is allow for transparency between all team members, accelerating turn around time for projects, or recovery efforts.

## Setting up ChatOps using Slack

Stackstorm provides a pack known as `st2chatops` which handles necessary setup, including setting up Hubot with the necessary adapters for Slack.

To configure ChatOps for Slack using `st2chatops`:

	1. Add a new Hubot integration to Slack
	2. Make a note of the of the `HUBOT_SLACK_TOKEN` that Slack provides
	3. Edit the file `/opt/stackstorm/chatops/st2chatops.env`, by:
		+ Uncommenting and updating the `HUBOT_SLACK_TOKEN` environment variable
	 	+ Uncommenting/Adding variables: `HUBOT_ADAPTER=slack`
	4. Restarting `st2chatops` with sudo service st2chatops restart
	5. Check that Hubot is connected by checking logs: `/var/log/st2/st2chatops.log` or `journalctl --unit=st2chatops`

## ChatOps Adding New ChatOps Commands Using Aliases

ChatOps uses Action **Aliases** to define how commands can be run by chatbots like Hubot
	- Aliases provide a more human readable representation of Actions

In order to add/allow an Action to be run through ChatOps, An alias yaml file needs to be provided for that action. For example:

```
---
name: "greet"
pack: "example_pack"
action_ref: "example_pack.greet"
description: "Greet StackStorm"
formats:
	- "greet {{greeting=Hello}}"

```
This is an alias for an example Action called "greet" which prints "{{ greeting }} Stackstorm!" where {{ greeting }} is a string passed into the action
This Action can be run from Slack using Hubot by running for example:
	- `!greet Hello` or `!greet`
Hubot will run the action and output
	- `Hello Stackstorm`

See Alias Structure section below for more information, or see Stackstorm Docs [Stackstorm Alias](https://docs.stackstorm.com/chatops/aliases.html)

Once an Alias is defined in a Pack, and installed, you must register new commands and reload Hubot
	`sudo st2ctl reload --register-aliases`
	`sudo service st2chatops restart`

## Alias Structure and Definition
An Alias is a simplified, more human readable method of invoking a Stackstorm Action

Aliases are defined in YAML files, and deployed in packs

All Aliases must contain the following properties

1. name: a unique identifier for the alias
2. action_ref: the action being aliased - in the format "pack.action_name"
3. formats: a list of all possible ways for users to invoke that action. For example:
```
formats:
	- "greet {{ greeting=Hello }}"
	- "(greet|say|echo) {{greeting=Hello} (S|s)tackstorm[!.]?"
```
Allows Jinja templating to extract inputs for the action - here we extract a string to represent "greeting" argument for Action "example_pack.greet"
Allows Regular expressions to match different methods of entry (Allowing "say" or "echo" to be entered)

Optional properties include:

4. parameters: a list of possible predefined inputs for the action
	- this can also be done using Jinja templating by providing a default e.g. "{{greeting=Hello}}"
```
parameters:
	greeting: "Hello"
```

5. immutable_parameters: a list of parameters which cannot be changed by the user
```
immutable_parameters:
	password: "{{ st2kv('system.slack_user_password', decrypt=true) }}"
```

6. display-representation: a way to better describe how to run a complex ChatOps command

By default, formats are provided as-is, including any complex regex/Jinja templating, which may be hard to understand
Instead, you provide a separate "display" and "representation" properties.

```
formats:
	- display: "greet {{greeting}} stackstorm!"
	  representation:
		- "greet {{ greeting=Hello }}"
        	- "(greet|say|echo) {{greeting=Hello} (S|s)tackstorm[!.]?"

```

display - is what is presented to the user when !help is invoked
representation - formats of the command of what Hubot tries to match

7. ack: How the chatbot acknowledges to the user that it has received a command
```
ack:
	format: "Executing `{{ actionalias.ref}}`, your ID is `{{ execution.id[:2] }}..{{ execution.id[:-2] }}`"
```
This acknowledge will print out a confirmation string of action alias reference invoked and the first and last 2 characters of the execution.id associated with this command in stackstorm  

8: result: Similar to ack - how the results of the action are outputted back to the chatroom
```
result:
	format: |Ran command *{{execution.parameters.cmd}}* on *{{ execution.result | length }}* hosts.

    		Details are as follows:
    		{% for host in execution.result -%}
        		Host: *{{host}}*
        	---> stdout: {{execution.result[host].stdout}}
        	---> stderr: {{execution.result[host].stderr}}
    	{%+ endfor %}
```
An example of how a result could be configured
Slack formats ChatOps output as attachments, and you can configure the API parameters using the result.extra.slack field
	- can pass in any properties defined in the [Slack API](https://api.slack.com/messaging/composing/layouts#attachments)

See more information at [Stackstorm Alias](https://docs.stackstorm.com/chatops/aliases.html)

Note: Stackstorm allows the user can pass in extra arguments as key-value pairs even if not specified by any of the possible formats
	- this will be passed on to the action
	- can be done by adding "(key1)=(value1)" when running a ChatOps command
