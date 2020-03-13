=======
BCO-DMO
=======

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
*  install into ``/var/local/dataone/miniconda_bcodmo_adapter``
*  **DO NOT** accept the option to initialize the miniconda environment; doing so will wreak havoc on all GMN environments because it changes the ``gmn`` user's initialization files.
*  Read the above warning one more time.  Do not even try to activate the environment.  Just rely upon the **PATH**.

Alter the **PATH** environment variable::

    PATH=/var/local/dataone/miniconda_bcodmo_adapter/bin:$PATH
    export PATH

Install the necessary 3rd party packages::

    conda install -c conda-forge --file conda-requirements.txt
    python -m pip install -r pip-requirements.txt

Apply a patch to a ``d1_scimeta`` file to fix an issue with validation of BCO-DMO XML files.  Replace 
``/var/local/dataone/miniconda_bcodmo_adapter/lib/python3.7/site-packages/d1_scimeta/schema_root/isotc211-noaa.xsd``
with the following content::

    <?xml version='1.0' encoding='utf-8'?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:import namespace="http://www.isotc211.org/2005/gco" schemaLocation="../schema/isotc211-noaa/gco/gco.xsd"/>
      <xs:import namespace="http://www.isotc211.org/2005/gmd" schemaLocation="../schema/isotc211-noaa/gmd/gmd.xsd"/>
      <xs:import namespace="http://www.isotc211.org/2005/gmi" schemaLocation="../schema/isotc211-noaa/gmi/gmi.xsd"/>
      <xs:import namespace="http://www.isotc211.org/2005/gmx" schemaLocation="../schema/isotc211-noaa/gmx/gmx.xsd"/>
      <xs:import namespace="http://www.isotc211.org/2005/gsr" schemaLocation="../schema/isotc211-noaa/gsr/gsr.xsd"/>
      <xs:import namespace="http://www.isotc211.org/2005/gss" schemaLocation="../schema/isotc211-noaa/gss/gss.xsd"/>
      <xs:import namespace="http://www.isotc211.org/2005/gts" schemaLocation="../schema/isotc211-noaa/gts/gts.xsd"/>
      <xs:import namespace="http://www.isotc211.org/2005/srv" schemaLocation="../schema/isotc211-noaa/srv/srv.xsd"/>
      <xs:import namespace="http://www.opengis.net/gml" schemaLocation="../schema/isotc211-noaa/gml311/gml.xsd"/>
      <xs:import namespace="http://www.w3.org/1999/xlink" schemaLocation="../schema/isotc211-noaa/xlink/xlinks.xsd"/>
      <xs:import namespace="http://eden.ign.fr/xsd/metafor/20050620/mf" schemaLocation="../schema/isotc211-noaa/mf/cargene.xsd"/>
      <xs:import namespace="http://eden.ign.fr/xsd/metafor/20050620/mf" schemaLocation="../schema/isotc211-noaa/mf/coverageMeasures.xsd"/>
      <xs:import namespace="http://eden.ign.fr/xsd/metafor/20050620/mf" schemaLocation="../schema/isotc211-noaa/mf/coverageType.xsd"/>
      <xs:import namespace="http://eden.ign.fr/xsd/metafor/20050620/mf" schemaLocation="../schema/isotc211-noaa/mf/measureType.xsd"/>
      <xs:import namespace="http://eden.ign.fr/xsd/metafor/20050620/mf" schemaLocation="../schema/isotc211-noaa/mf/metafor.xsd"/>
      <xs:import namespace="http://eden.ign.fr/xsd/metafor/20050620/mf" schemaLocation="../schema/isotc211-noaa/mf/mfExtensions.xsd"/>
    </xs:schema>

This same file must be updated on the GMN server as well!

Install the SlenderNode adapter::

   cd SlenderNodes/schema_org
   python setup.py install

Create a script for running the adapter in ``/var/local/dataone/minconda_bcodmo_adapter``.  Here is such a script::

    #!/bin/bash

    set -x
    set -e

    D1=/var/local/dataone
    PATH=$D1/miniconda_bcodmo_adapter/bin:/usr/bin:/bin

    # This assumes that the certs are installed as listed below.
    harvest-bcodmo \
        --host gmn.test.dataone.org \
        --max-num-errors=100 \
        --certificate $D1/certs/client/urn_node_mnTestBCODMO/urn_node_mnTestBCODMO.crt \
        --private-key $D1/certs/client/urn_node_mnTestBCODMO/private/urn_node_mnTestBCODMO.key 

It is expected that the script will take over 6 hours to run the first time.  The number of errors being allowed is large, but there does seem to be a large number of ``500`` HTTP errors being thrown on the BCO-DMO side.  After each run, you may check the logs at ``/var/local/dataone/miniconda_bcodmo_adapter/bcodmo.log``.
