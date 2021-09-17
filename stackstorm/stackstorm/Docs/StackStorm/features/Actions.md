# StackStorm Actions

Actions perform arbitrary tasks.
Stackstorm allows Actions to be written in any scripting language Python, Bash, Perl etc.

It is convention to use Python to write Actions.

## Managing and Running Actions

Stackstorm uses Packs to bundle together Sensors, Actions, Aliases and Rules.

To run or access an Action, you must specify the Pack name it belongs to:
`Pack_Name.Action_Name`

For example:
`Stackstorm_openstack.show.user`
Where the Pack name is `Stackstorm_openstack` and the Action name is `show.user`


An Action is run in the CLI with this command:
`st2 run <Pack_name.Action_Name> Arg1=Val1 Arg2=Val2 Arg3=Val3`
This action will run in the foreground, to run in the background, use:
`st2 action execute <Pack_Name.Action_Name> Arg1=Val1 ...`
This schedules an Action execution and runs in the background

To access the logs of Actions executed in the background or previously executed actions:
`st2 execution get <execution.id>`
To access just the raw tail output:
`st2 execution tail <execution.id>`

To get the properties of an Action, such as arguments, script location and description, use:
`st2 action get Pack_Name.Action_Name`

To list all available actions:
`st2 action list`
Can also filter this list by pack:
`st2 action list --pack Pack_Name`

## Creating Actions

In order to write a StackStorm Action, you must create or edit an existing Pack

An Action is composed of two components
	- YAML metadata file - describing the action and its inputs
	- A script which implements the action logic - usually written in Python


### The Action Script
Action Scripts should terminate with a 0 status code on success, or a non-zero status code on failure

A Python Script

Written as a class which inherits from `st2common.runners.base_action.Action` class

The logic of the script must be defined in the `run` method.
This method is called by StackStorm with all input arguments entered when the action is successfully invoked

	- If the `run` method terminates without exceptions, the execution is marked as successful in StackStorm.
	- Raising an exception whilst running means the execution is marked as failed in StackStorm

Another way of explicitly defining status of execution is by returning a tuple where:
	- the first item is a Boolean indicating execution status - True=Success, False=Failed
	- the second item is the actual result `dict, string, int`, etc.

#### Logging
All logging inside the action should be performed via the logger specific to the action - accessed using the `self.logger` attribute
The logger is a standard Python logger from the `logging` allowing methods like `logging.info` and `logging.debug`

#### Datastore and Config Access
You can access the config elements of the pack within a Python action using `self.config` - accessed as a Python dictionary
To access other elements in the datastore you can use `self.action_service`

### The Action Metadata
All Actions need an Action Metadata YAML file to register themselves in StackStorm

Each Action Metadata file requires:
`name`: Name of the Action
`runner_type`: what type of Action Script the Action uses
One of:
	- `local-shell-script` (local bash script)
	- `remote-shell-script` (remote bash script)
	- `python` (Python script)
	- `orquesta` (Orquesta workflow)

`description`: Description of Action
`enabled`: True/False if Action should be registered in StackStorm as callable
`entry_point`: Relative file path to Action Script
`parameters`: Input Parameters for the Action
Each Input parameter is defined as:

```
	key1:
	    type: "string"	# (Optional) Can be "string", "integer", "float", "boolean", "array" or "object"
	    required: true	# Whether the parameter is optional or not
	    default: ""		# (Optional) Default value if not given
	    description: ""	# (Optional) Description of what the input is
	    immutable: false	# (Optional, default=false) If the parameter is immutable (cannot be changed by user - must specify default if True))
```

# Creating A New Pack

A Pack is a unit of deployment in Stackstorm - it contains a set of interrelated Actions, Workflows, Rules, Sensors and Aliases.
Typically, a pack is organised along service or product boundaries

A typical pack has the following file structure:
```
actions/ 		# action subdirectory
rules/			# rules
sensors/		# sensors
aliases/		# aliases
policies/		# policies
etc/			# other scripts/config files
config.schema.yaml	# pack config schema
packname.yaml.example	# pack config example
pack.yaml		# pack definition
requirements.txt	# pack requirements for Python
```

`pack.yaml`: Metadata file which describes and identifies the folder as a Stackstorm Pack
`config.schema.yaml`: Optional Pack Configuration elements - stored in Stackstorm Datastore
`requirements.txt`: File containing a list of Python dependencies.
	- Each pack has its own Python virtualenv, so any specific Python libraries used will need to be specified here and will be automatically installed using `pip` at pack install time

### The Pack definition file

The Pack definition file is a yaml file contains:

1. `ref`: pack reference, it can only contain lowercase letters - used to identify the pack if `name` contains special characters
2. `name`: name of the pack
3. `description`: user-friendly pack description
4. `keywords`: a list of words describing the pack, helpful when searching for packs
5. `version`: the version of StackStorm being used <major>.<minor>.<patch> e.g. 1.0.0
6. `python_versions`: the Python versions the pack will use
7. `dependencies`: A list of other Packs dependencies to install (can use "name" if the pack is in Stackstorm Exchange, else specify a full git repository url (with optional version, tag or branch))
8. `author`: Name of the pack creator
9. `email`: Email of pack creator
10. `contributors`: list of additional contributors

### Installing the Pack

Once the pack is created and a number of Sensors, Actions, Rules, Aliases etc. are created - the pack can be installed

It is encouraged to use git for version control whilst developing a Pack:
`cd path/to/pack`
`git init && git add ./* && git commit -m "initial commit"`

Then you can install the pack using:
`st2 pack install $(pwd)`

Once completed, check if the pack is registered:
`st2 pack list`
and then check if all the Pack contents are registered
`st2 action list`
`st2 rule list`
`st2 trigger list`

If you have written a config schema, and a corresponding example yaml file - you will need to:
	1. Copy the example yaml file into `opt/StackStorm/configs/` and rename it to `<your_pack_name>.yaml`
	2. Reload and Register the new config file `sudo st2ctl reload --register-configs`
