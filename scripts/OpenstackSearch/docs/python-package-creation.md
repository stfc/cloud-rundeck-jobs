### Creating a PIP Installable Python Package

#### Introduction

PIP - A package installer and management system, specifically designed
for installing Python packages from the internet.
PIP uses the Python Package Index (PyPI) to download packages - however,
you can use pip to install user-defined packages

A Python package needs to consist of:
  - a root directory - usually with the name of the package.
  - a sub-directory containing the scripts and modules that make up the package.
  - a file called `__init__.py` in the same sub-directory alongside the scripts and modules
      - this file denotes the directory as a python package - it can be empty
      - when running `pip install` this directory will be installed and become importable
      - a separate `__init__.py` is required for each sub-package
  - at the root directory - a file called `setup.py`
      - this will govern how to install the package
      - the python package `setuptools` is recommended for this (the older
        built-in alternative package `distutils` can also be used)

E.g. A simple project may have this structure

```
query_openstack
├── queryopenstack
│   ├── __init__.py
│   ├── search.py
│   ├── utils.py
│   └── classes
│         ├── __init__.py
│         ├── list_items.py
│         ├── list_servers.py
│         ├── list_hosts.py
│         ├── list_ips.py
│         ├── list_projects.py
│         ├── list_users.py
└── setup.py
```

#### Creating Setup.py

At the root directory of your python package, a `setup.py` file is needed. This
file is used to govern the details of PIP installation. In this tutorial we will
use the `setuptools` package to handle the setup routine.

`pip install setuptools`

The main requirement of `setup.py` is to provide project information as keyword
arguments. A lot of different information can be provided. An example of a
setup.py can be seen below:
```
from setuptools import setup, find_packages

setup (
        name="queryopenstack", # should be same as sub-directory containing package
        version='0.0.1',
        author="Anish Mudaraddi",
        author_email="anish.mudaraddi@stfc.ac.uk",
        description='query and list openstack compute services',
        packages=find_packages(), # finds all subpackages automatically
        python_requires='>=3',
        install_requires=["openstacksdk", "tabulate"], # list package dependencies
        keywords=['python', 'openstack']
)
```
More information about setup options can be found in the [PyPA User Guide](https://packaging.python.org/tutorials/packaging-projects/)

Note: if you want to create sub-packages, they should ideally be directories
inside the main package. But re-mapping from other locations is possible during
setup using the package_dir argument. All sub-packages require their own
`__init__.py` in the directory.

#### Installation

Having created a `setup.py`, you can install the package with pip. In the root
directory, run:

`pip install .`

If you want to ensure package and dependencies are updated use `--upgrade`

To uninstall the package, run:

`pip uninstall <packagename>`

Note: if you want to provide package attributes like `__version__` and
`__author__`, you must define them in the `__init__.py`. Although this
introduces a problem of ensuring the two places use the same version number.
