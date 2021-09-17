# Orquesta

Orquesta is a graph-based workflow engine designed to run natively on StackStorm
Orquesta can support complex workflows with forks and joins

An Orquesta workflow is treated as an Action in StackStorm, hence requires:
	- A Metadata file
	- An Orquesta workflow YAML definition file

This metadata file requires `action_runner: Orquesta` in order to tell StackStorm that it is an Orquesta workflow


## The Workflow definition file

The workflow definition is syntactic sugar representing a directed graph

Orquesta converts the workflow definition into a directed graph of Actions to perform
	- Nodes in the graph represents Actions to perform (Tasks)
	- Edges represent conditions to match in order to execute the next subsequent Action (Task Transitions)

Each task represents one step in the workflow and consists of:
	- A Stackstorm action to execute
	- Inputs for that action
	- Criteria to transition to other tasks
	- Each Task can optionally publish outputs of the action to be used by subsequent tasks

When running the workflow, Orquesta's workflow conductor is used to:
	1. Traverse the graph, identifying and directing the flow of execution
	2. Schedules the action to be run by StackStorm, and tracks runtime state of the execution
	3. As each action completes, StackStorm relays the status and result back to the conductor as an event
	4. The conductor processes the even, keeping track of execution history. It updates the runtime context, and repeats the loop until all tasks completes

	5. Once all tasks complete, or when execution fails, the conductor determines the overall workflow status and results
		- StackStorm propagates any failure in any step to stop any parallel processes and stops execution

		- If the workflow failed, the conductor will output results from the latest version of the runtime context

The Orquesta workflow engine is designed to fail fast and terminate the execution of the workflow when a task fails.
If a task fails, the workflow waits for all currently running tasks in other branches to finish and then terminates without running/scheduling subsequent tasks

## Workflow Attributes

The following attributes make up the workflow model:

  - `version` (Required) - the version of the spec being used in this workflow
  - `description` - the description of the workflow
  - `input` - a list of input arguments for the workflow
  - `vars` - a list of global variables available to all tasks in workflow
  - `tasks` (Required) - a dictionary of tasks, defining the intent of the workflow
  - `output` - a list of variables defined as output of the workflow

A Orquesta `task` can have the has the following attributes:

  - `delay` - the number of seconds to delay the task execution

  - `join` - if specified, sets up a barrier for a group of parallel branches
      - ensures all parallel branches that lead to this task terminate before executing task    
      - the task for which join is known as a "barrier task", it ensures only one instance of this task is created in the workflow graph
      - if join is not specified, and more than one tasks transition to this task, it will be invoked immediately, with multiple instances in the workflow task.
      - `join: all` - default, waits until for all task transitions
      - `join: <integer>` - waits for n tasks to transition before task is executed

  - `with` - when given a list, execute the action for each item in parallel
      - when this action is cancelled or paused, by default the task will wait until all executions are completed before cancelling or pausing.
	if `concurrency` is defined no new actions will be scheduled.

      - `concurrency` - limit number of parallel processes
      - `items` (Required) - the list of items to execute the action with

  - `action` - the fully qualified name of the action to be executed

  - `input` - a dictionary of input arguments for the action execution

  - `retry` - if specified, define requirements for a task to be retried
      - `when` - criteria defined as an expression required for retry
      - `count` (Required) - number of times to retry
      - `delay` - the number of seconds to delay in between retries

  - `next` - defines the task transitions to be evaluated after action completes
      - `when` - criteria defined as an expression, evaluated after the action, for transition
      - `publish` - a list of key-value pairs to be published into the context
      - `do` - a next set of tasks to invoke when transition criteria is met, each task transition is represented as outbound edges of the current task

## Engine Commands
The following is a list of engine commands:

  - `continue` - default value when do is specified. Tells workflow engine to continue to conduct workflow execution. if the previous task state is a fail, the conductor will terminate workflow execution

  - `fail` - workflow engine will fail the workflow execution

  - `noop` - workflow engine will perform a task with no action (no-operation).
