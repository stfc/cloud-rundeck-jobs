# StackStorm Packs

A Pack is a unit of deployment in Stackstorm - it contains a set of interrelated Actions, Workflows, Rules, Sensors and Aliases.
Typically, a pack is organised along service or product boundaries

A typical pack has the following file structure:
```
actions/                # action subdirectory
rules/                  # rules
sensors/                # sensors
aliases/                # aliases
policies/               # policies
etc/                    # other scripts/config files
config.schema.yaml      # pack config schema
packname.yaml.example   # pack config example
pack.yaml               # pack definition
requirements.txt        # pack requirements for Python
```

`pack.yaml`: Metadata file which describes and identifies the folder as a Stackstorm Pack
`config.schema.yaml`: Optional Pack Configuration elements - stored in Stackstorm Datastore
`requirements.txt`: File containing a list of Python dependencies.
        - Each pack has its own Pyhton virtualenv, so any specific Python libraries used will need to be specified here and will be automatically installed using `pip` at pack install time

## The Pack definition file

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


# StackStorm Datastore

StackStorm has a Datastore which is used to store parameters and values that are likely to be reused by Sensors, Actions and Rules

The datastore stores data as key-value pairs. They can be accessed within Action or Sensor Scripts or within metadata YAML files.

They can also be added/edited using StackStorm CLI:
```
st2 key list						# lists first 50 key-value pairs
st2 key list -n -1 					# lists all key-value pairs

st2 key set example_key example_value -ttl=3600		# Adding a key-value pair to the datastore, with a time to live of 1 hour
```

They can also be loaded from a YAML or JSON file with:
`st2 key load example.json`
```
# example.json JSON file
[
    {
        "name": "example_key"
        "value": "example_value"
    }
}
```

```
# example.yaml YAML file
---
- name: example_key
  value: example_value
```

By default all values in Datastore are serialised and stored as Strings.
To pass in a integer value use Stackstorm's in-built converter
`st2 key set example_key 10 --convert`

You can access the Datastore in YAML metadata files and pass them as arguments for Actions, Sensors or Rules using Jinja or YAQL

Can access the datastore using `st2kv`
YAQL: `<% st2kv.system.example_key %>`
Jinja: `{{ st2kv.system.example_key }}`

```
val1:
    type: "string"
    description: "test value"
    default: "{{ st2kv.system.val1 }}"
```

Or you can access the key-value storage directly in Action or Sensor scripts using `self.action_service` or `self.sensor_service`
`test_value = self.action_service.get_value("test_key")`
`self.action_service.set_value("cache", json.dumps(cache))`


## Secrets
Datastore uses secrets to store sensitive information such as passwords

Secrets are encrypted values.
StackStorm uses AES-256 symmetric encryption to encrypt secrets.

To generate a symmetric crypto key, run:
`sudo mkdir -p /etc/st2/keys/`
`sudo st2-generate-symmetric-crypto-key --key-path /etc/st2/keys/datastore_key.json`

Then edit the st2 config file `/etc/st2/st2.conf/` and add the following lines
```
[keyvalue]
encryption_key_path = /etc/st2/keys/datastore_key.json
```

Then restart Stackstorm with `sudo st2ctl restart`

Then you can add/get secrets:
`st2 key set password secret_password --encrypt`
`set key get password --decrypt 	# running without --decrypt returns encrypted string`


You can access and pass in secrets as inputs to Stackstorm Actions, Rules or Sensors by using Jinja in YAML metadata files
```
password:
    type: "string"
    immutable: True
    default: "{{ st2kv.system.password | decrypt_kv }}"
```

Or you can access them in the same way as other data-storage items using `self.action_service` or `self.sensor_service` (but require a `decrypt=True` flag)


# Pack Configuration

A pack often requires extra configuration parameters.
The structure of the config file is defined in the config schema for the Pack
The Config Schema is a YAML file which contains information about every configuration parameter for the pack (name, type, if a secret etc.)

Note: You can define configuration items as Secrets (encrypted values) by giving the item the property: `secret: True`

Once a config schema is defined, you can define each parameter using the command:
`st2 pack config <Pack_Name>`
This will generate a simple text-based UI to allow you to enter each config parameter one at a time

You can instead write a corresponding example yaml file for the Pack to define a set of default parameter values - you will need to:
	1. Copy the example yaml file into `opt/StackStorm/configs/` and rename it to `<your_pack_name>.yaml`
	2. Reload and Register the new config file `sudo st2ctl reload --register-configs`
