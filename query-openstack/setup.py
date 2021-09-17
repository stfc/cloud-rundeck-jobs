from setuptools import setup, find_packages

VERSION = '0.0.1.dev1'
DESCRIPTION = 'query and list openstack compute services'

LONG_DESCRIPTION = """Query and list openstack compute services
- for users, servers, ips, hypervisors and projects
based on a set of predefined criteria"""

setup (
        name="queryopenstack",
        version=VERSION,
        author="Anish Mudaraddi",
        author_email="<anish.mudaraddi@stfc.ac.uk>",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        python_requires='>=3',
        install_requires=["openstacksdk", "tabulate"], # add any additional packages that
        # needs to be installed along with your package. Eg: 'caer'
        keywords=['python', 'openstack']
)
