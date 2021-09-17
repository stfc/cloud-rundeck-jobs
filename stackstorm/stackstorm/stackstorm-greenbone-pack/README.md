# Stackstorm-greenbone-pack
A Stackstorm pack for Greenbone integration
A collection of Stackstorm actions to handle sending vulnerability information from Greenbone scans to users

# Setup SQLite Database

First run the Greenbone scan, and save outputted csv file in a location accessible by the machine running stackstorm

Then run the following command:
`st2 run stackstorm_greenbone.create.and.populate.greenbone.db db_file_path="/path/to/db/dir" csv_path_list=/path/to/csv/ csv_path_list=/path/to/csv2/ ...`

This will create an SQLite database with filepath matching that given in `db_file_path`: default is `/home/<user>/greenbone/Greenbone.db`, and will populate the DB with a list of csv files if found in the filepaths given. These csv files must be the outputs of greenbone scans

Alternatively, you can run:

`python {path_to_repo}/src/Create_DB.py --target_directory "/path/to/dir"`
`python {path_to_repo}/src/Populate_DB.py --db_filepath "/path/to/database/Greenbone.db" --csv_filepath "/path/to/greenbone/csv"`

This will populate the database with greenbone scan information. It requires an Openstack connection in order to get "User ID" and "VM age" information


# Greenbone Workflows

`create.and.populate.db` - Workflow to build the SQL Database and populate it with a number of greenbone scan csv files.
	- Run once during setup. Once the DB is built, further scans can be added to the database using `populate.greenbone.db` action

Required Parameters:
- `csv_path_list`: An array of csv filepaths which contain greenbone scan information

Optional Parameters:
- `db_file_path`: A filepath to a location where the new Greenbone database will be created
	- default: `/home/<user>/greenbone/Greenbone.db`


`send.vulnerability.email.admin` - Workflow to send emails of vulnerability information intended for admins. (Only "Critical" or "High" level vulnerabilities)
This is any greenbone db information where:
	1. Have `IP_Status` set to "Inactive"
  	2. Have `IP_Status` set to "Server_Changed"
  	3. Have `Resource_ID` set to "NULL" (I.e. Not Found in Openstack)
  	4. Have `User_ID` set to NULL (I.e. User Not Found in Openstack)
	5. Are Found to be Hypervisors in Openstack

Required Parameters: None
Optional Parameters:
- `db_file_path`: A filepath to a location where the new Greenbone database will be created
	- default: `/home/<user>/greenbone/Greenbone.db`

- `email_from`: Email addresses to send email from
	- default: `cloud-support@gridpp.rl.ac.uk`

- `header`: filepath to header file
	- default: `path/to/repo/src/html_files/header`

- `footer`: filepath to footer file
	- default: `path/to/repo/src/html_files/footer`

- `subject`: subject for email
	- default: "Information: Greenbone Scan Results Have Identified Critical or High Vulnerabilities Needing to be Patched"  

- `smtp_account`: SMTP account to use which are stored in config
	- default: "default"

- `attachments_tmp_dir_path`: Directory path to store temporary csv attachment files
	- default: `home/<user>/tmp`

- `send_html`: Boolean to send email body as html or as plaintext
	- default: True


`send.vulnerability.email` - Workflow to get all "User IDs" that are stored in the Greenbone Database which are associated with Servers that have "Critical" or "High" level vulnerabilities
	- This is any information where `IP_Status`is set to "active" AND `User_ID` is found in Openstack

Required Parameters: None
Optional Parameters:
- `db_file_path`: A filepath to a location where the new Greenbone database will be created
	- default: `/home/<user>/stackstorm_workspace/greenbone/Greenbone.db`

- `email_from`: Email addresses to send email from
	- default: `cloud-support@gridpp.rl.ac.uk`

- `header`: Filepath to header file
	- default: `/home/<user>/stackstorm_workspace/html_files/header.html``

- `footer`: Filepath to footer file
	- default: `/home/<user>/stackstorm_workspace/html_files/footer.html``

- `subject`: Subject for email
	- default: "Greenbone Scan Results: Critical or High Vulnerabilities"  

- `smtp_account`: SMTP account to use which are stored in config
	- default: "default"

- `attachments_tmp_dir_path`: Directory path to store temporary csv attachment files
	- default: `home/<user>/stackstorm_workspace/tmp`

- `send_html`: Boolean to send email body as html or as plaintext
	- default: True

- `admin_override`: Boolean to override where to send emails - for testing purposes
	- default: True 	# must be changed in PROD

- `admin_override_email`: Email to send to if admin override is True
	- default: "jacob.ward@stfc.ac.uk"

# Greenbone Actions

Has the following Actions:

Atomic actions that call Python Scripts:

`create.csv.file` - Action to create a csv file to store vulnerability information. (Only "Critical" or "High" level vulnerabilities)
	- To be attached to emails

`get.all.user.ids` - Action to get all "User IDs" that are stored in the Greenbone Database which are associated with Servers that have "Critical" or "High" level vulnerabilities
	- Used to search openstack to validate and get emails

`get.info.for.admin` - Action to get all vulnerability information intended for admins. (Only "Critical" or "High" level vulnerabilities)

`get.info.for.user` - Action to get all vulnerability information for a given user. (Only "Critical" or "High" level vulnerabilities)

`populate.greenbone.db` - Action to populate an existing Greenbone Sqlite3 DB

`create.greenbone.db` - Action that creates an empty Greenbone Sqlite3 DB

 # Misc

See `/pics` folder for entity relationship diagram for sqlite database used
