===
ARM
===

***********************************
Installation in Staging Environment
***********************************

SSH into ``gmntest.test.dataone.org``.

Become the gmn user::

   sudo -Hsu gmn

Clone the repo::

   git clone https://github.com/jevans97utk/SlenderNodes.git

Download miniconda from continuum.io::

   wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

Create the anaconda environment::

   bash Miniconda3-latest-Linux-x86_64.sh

*  accept the license
*  install into ``/var/local/dataone/miniconda_arm_adapter``
*  **DO NOT** accept the option to initialize the miniconda environment; doing so will trip up all GMN environments
*  Read the above warning one more time.  Do not even try to activate the environment.  Just rely upon the **PATH**.

Alter the **PATH** environment variable::

    PATH=/var/local/dataone/miniconda_arm_adapter/bin:$PATH
    PATH=/var/local/dataone/miniconda_arm_adapter/envs/slendernode/bin:$PATH
    export PATH

Create the **slendernode** anaconda environment.::

    conda env create -n slendernode --file SlenderNodes/schema_org/environment.yml

Install the slendernode adapter::

   cd SlenderNodes/schema_org
   python setup.py install

Create a script for running the adapter in ``/var/local/dataone/minconda_arm_adapter``.  Here is such a script::

    #!/bin/bash

    set -x
    set -e

    D1=/var/local/dataone
    PATH=$D1/miniconda_arm_adapter/envs/slendernode/bin:/usr/bin:/bin

    harvest-arm \
        --host gmn.test.dataone.org \
        --certificate $D1/certs/client/urn_node_mnTestARM/urn_node_mnTestARM.crt \
        --private-key $D1/certs/client/urn_node_mnTestARM/private/urn_node_mnTestARM.key 

