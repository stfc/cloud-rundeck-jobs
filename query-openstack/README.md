# Query-Openstack
A python package to allow querying of Openstack resources using python openstacksdk.

This package handles complex Openstack queries in just one function call. Without needing to write complex bash scripts.
  - pretty prints only the information required to the console (using tabulate)
  - can store this information as a csv file

Currently the package allows the user to query by the following Openstack resources:
    - VMs (Servers)
    - Users
    - Hypervisors (Hosts)
    - Projects
    - Floating Ips

# Installation
Must have `Python3` and `pip` installed and updated (you may also need to install the latest version of the `cryptography` python module)

To install the Python package, clone the repository and run:

`pip install /path/to/repo/`

The package and all of its pre-requisites will be installed to
`/path/to/python/site-packages` directory.

By default, the package will attempt to open an openstack connection by using
credentials located in a config file called `clouds.yaml` located at `~/.config/openstack/` or `/etc/openstack/`.

If this file/directory doesn't exist, the query will be aborted.
You can get around this by specifying your own `openstack.connection.Connection`
object as a parameter when calling `queryopenstack.query.Query()`

# search_openstack.py Usage
The python script `search_openstack.py` located at `/path/to/repo/examples/`
provides an example of how to interface with the package.
This script takes CLI arguments to run a query, for example:   

`python search_openstack.py server
--select server_id server_name user_id user_name --where id 1 2 3 4 5
--where status ERROR --where has-illegal-connections
--no-output --sort-by server_name --save --save-in "path/to/dir/name.csv"`

The CLI given are explained below:

- `server` - (positional argument) refers to searching for VMs on the network - currently possible valid arguments are:
- `host` - search for Hypervisors
- `user` - search for Users
- `project` - search for projects
- `ip` - search for floating ips

- `--select` - refers to properties of the openstack resource that are to be outputted - multiple properties can be given here in sequence with whitespace as a delimiter

- `--where` - refers to conditions/criteria each openstack resource must match. Act as filters to refine the query.
  - format is `--where "NAME OF CONDITION" ARG1 ARG2`
  - multiple `--where` inputs can be given - acts as an AND operator


- `--sort-by` - refers to fields to sort the output by

- `--save` - toggles on saving output of query into text file
  - file is delimited with a whitespace

- `--save-in` - specified filepath to save file into

- `--no-output` - toggles off pretty printing to console
