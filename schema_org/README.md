Slender Node Adapter Supporting schema.org described Resources
==============================================================

Notes for implementation of a "slender node" adapter to support synchronization
of content described with schema.org constructs.

# ARM instructions

1. Become the gmn user, `sudo -Hsu gmn`
2. `git clone https://github.com/jevans97utk/SlenderNodes.git`
3. Download miniconda from continuum.io, `wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh`
4. Create the anaconda environment, `bash Miniconda3-latest-Linux-x86_64.sh`
   1.  accept the license
   2.  install into /var/local/dataone/miniconda_arm_adapter
   3.  **DO NOT** accept the option to initialize the miniconda environment; doing so will trip up all GMN environments
5. Alter the **PATH** environment variable

```
PATH=/var/local/dataone/miniconda_arm_adapter/bin:$PATH
PATH=/var/local/dataone/miniconda_arm_adapter/envs/slendernode/bin:$PATH
export PATH
```

Be aware that once this path is set, you cannot clear the database and _start over_.  If you need to do that, you should do so in another terminal window without altering the path.

6. Create the **slendernode** anaconda environment

```bash
conda env create -n slendernode --file SlenderNodes/schema_org/src/environment.yml
```

7. Install the slendernode adapter
   1. `cd SlenderNodes/schema_org/src`
   2. `python setup.py install`

8. Create a script for running the adapter in `/var/local/dataone/minconda_arm_adapter`.  Here is such a script.

```bash
#!/bin/bash

set -x
set -e

D1=/var/local/dataone
PATH=$D1/miniconda_arm_adapter/envs/slendernode/bin:/usr/bin:/bin

harvest-arm \
    --host gmn.test.dataone.org \
    --certificate $D1/certs/client/urn_node_mnTestARM/urn_node_mnTestARM.crt \
    --private-key $D1/certs/client/urn_node_mnTestARM/private/urn_node_mnTestARM.key 
```

# Commandline executables

The following commandline utilities are included in this package and require Python 3.7.

* d1-validate - validates a single XML document against DataOne-supported formats
* d1-check-site - validate XML documents located through a sitemap URL
* harvest-adbs-ipt - harvest XML documents from the Arctic Biodiversity Data Service IPT RSS feed
* harvest-arm - harvest XML documents from the ARM Climate Research Faciility
* harvest-cuahsi - harvest XML documents from CUAHSI's Hydroshare online collaboration environment
* harvest-ieda - harvest XML documents from the Interdisciplinary Earth Data Alliance (IEDA) 
* harvest-nkn - harvest XML documents from the Northwest Knowledge Network (University of Idaho)

Install the utilities as follows:
>>>>>>> evans/master
```
$ python setup.py install
```

This will install two command-line utilities, harvest-ieda and harvest-arm, that may be used to harvest IEDA and ARM metadata.

```
$ harvest-ieda -h
usage: harvest-ieda [-h] [-v {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                [--host HOST] [--port PORT] [--certificate CERTIFICATE]
                [--key KEY]

Harvest metadata from IEDA.

optional arguments:
  -h, --help            show this help message and exit
  -v {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --verbose {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Verbosity level of log file ieda.log (default: INFO)
  --host HOST           Harvest records to this dataone node host. This is NOT
                        the host where the site map is found. (default:
                        localhost)
  --port PORT           DataONE host SSL port. (default: 443)
  --certificate CERTIFICATE
                        Path to dataone host certificate. (default: None)
  --key KEY             Path to dataone host private key. (default: None)

Not supplying an argument to both the certificate and key arguments will
disable client side authentication.
```

Discovery Pattern
-----------------

The general pattern for discovery of schema.org resources given a domain name is:

1. parse http(s)://domain.name/robots.txt

   This step is optional if the location of the sitemap.xml is known (step 2)

2. Get the sitemap.xml file from the location identified or inferred from robots.txt

3. For each entry in the sitemap.xml file:

   a. If the entry is sitemap, go to step 2 and process the referenced sitemap.

   b. Otherwise, load and parse the resource, extract the schema.org information

   c. If sufficient and appropriate schema.org information is available, then add the
      referenced resource or resources to the set of items to be processed. Note that
      the sitemap.xml may point to Dataset or a DataCatalog instance. In the latter case,
      the DataCatalog item should be processed to discover the contained Dataset
      instances.

A schema.org Dataset instance is considered to be the target item for synchronization by
DataONE, and the Dataset should contain references to the components of the Dataset.

DataONE treats the Dataset instance as a view of the actual dataset, with parts of the
view populated from difference components of the dataset such as the metadata and
resource map or its equivalent providing relationships between components.


Dataset Constructs
------------------

This content is in DRAFT status, subject to change.

Required properties:

* identifier
* datePublished
* dateModified  (required if there are updates after datePublished)
* distribution

The distribution element must be an array of DataDownload entries, one for each component
of the dataset being desribed.

Each entry in distribution should include:

* identifier
* encodingFormat
* name
* url
* "additionalType": "http://www.w3.org/ns/dcat#DataCatalog"



