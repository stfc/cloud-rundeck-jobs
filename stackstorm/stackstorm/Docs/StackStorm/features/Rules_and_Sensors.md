# Sensors

Sensor are a way to integrate external systems and events with StackStorm
Sensors can work in two different ways:
	- Periodically poll an external system
	- Passively wait for inbound events

Sensors work by: 
	1. Inject triggers into StackStorm
	2. Triggers are matched by rules
	3. Rules can then call Action executions

Sensors are written in Python.

Sensors inherit from `st2reactor.sensor.base.Sensor` and have the following structure
```
class SampleSensor(Sensor):
    
    def setup(self):
        # Setup stuff goes here
        # called only once by StackStorm
        pass
   
    def run(self):
        # This is where the sensor logic goes
        # Called once by StackStorm and should continually loop
        pass

    def cleanup(self):
        # Called when StackStorm crashes or turns off
        # cleanup operations
        pass

    def add_trigger(self, trigger):
        # This method is called when trigger is created
        pass

    def update_trigger(self, trigger):
        # This method is called when trigger is updated
        pass

    def remove_trigger(self, trigger):
        # This method is called when trigger is deleted
        pass
```

Sensor runs as a separate process, the `st2sensorcontainer` starts `sensor_wrapper.py` which wraps any Sensor classes

Each Sensor is passed a `sensor_service` on instantiation - this allows the Sensor to call a number of operations including:

`self.sensor_service.dispatch()` - which dispatches a trigger to StackStorm
`self.get_logger()` - allows the sensor to retrieve the logger instance specific to that sensor

`self.sensor_service.list_values(local=True, prefix=None) 	# list values in datastore (with local scope for that sensor)`
`self.sensor_service.get_value("test_key", local=False, decrypt=False) 	# get value from datastore `

## Running a Sensor

1. Place the Sensor Python file and YAML metadata file in a Pack, i.e the `default` Pack
2. Register the sensor by running `st2ctl reload --register-all

To run or debug a single sensor already registered you can run:
`sudo /opt/stackstorm/st2/bin/st2sensorcontainer --config-file=/etc/st2/st2.conf --sensor-ref=pack.Sensor_Class_Name`

## Sensor Troubleshooting

1. Verify that the sensor is registered
`st2 sensor list`

if not listed, then re-register the sensor 
`sudo st2ctl reload --register-sensors --register-fail-on-failure --verbose`
The `--register-fail-on-failure` and `--verbose` flags will print failure in case registration of particular sensor fails

2. Verify Virtual Environment Exists
Confirm that virtual environment has been created for that sensor pack
`st2 run packs.setup_virtualenv packs=<Pack_Name>`

3. Check st2sensorcontainer logs
Run the sensor container service in the foreground and debug in single sensor mode
`sudo /opt/stackstorm/st2/bin/st2sensorcontainer --config-file=/etc/st2/st2.conf --sensor-ref=pack.Sensor_Class_Name`


# Triggers

Triggers are StackStorm constructs that identify the incoming events 
	- a trigger is a tuple of type (string) and optional parameters 

Triggers are usually registered by the Sensor that dispatches them

To Register a Trigger, you must provide the following in the Sensor metadata under the `trigger_types` field (which holds an array triggers for that sensor)
`name`: Name of the trigger
`description`: (Optional) description of what the trigger is for
`payload_schema`: The metadata information for trigger parameters 

# Rules

Rules are defined in YAML. 
Rule definition structure has the following elements:
`name`: name of the rule
`pack`: pack the rule belongs to
`description`: description of the rule
`enabled`: if the rule is enabled 
`trigger`: the trigger name the rule aims to match
`criteria`: A set of criteria required for the trigger to match in order to execute corresponding Action. Consists of:
	- An attribute of trigger payload
	- `type`: what comparison is being made
	- `pattern`: to match against
`action`: the action to execute upon match. Consists of
	- `ref`: action name
	- `parameters`: a set of parameters to pass to the action execution

## Rule Criteria

To achieve a logical AND, multiple criteria within a rule represent a logical AND
To achieve a logical OR requires writing multiple rules with different criteria but with the same Action execution

see [Stackstorm Rules Docs](https://docs.stackstorm.com/rules.html) about different `types` for matching

