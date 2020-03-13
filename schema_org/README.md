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
```
$ python setup.py develop
```

## General Architecture

Despite this directory being named ``schema_org``, not all of the executables use Schema.Org.  There is some core functionality concerning asynchronous I/O that all 

In fact, only the ARM harvester can be described as the real deal w.r.t. both Schema.Org and sitemaps.  The Hydroshare/CUAHSI and IEDA harvesters use some Schema.Org functionality, but do not use all.


## Commandline Help
In each case, the harvesters all have a similar commandline interface.  For example, ``harvest-arm`` has the following help:

```
usage: harvest-arm [-h] [-v {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--host HOST]
                   [--port PORT] [--certificate CERTIFICATE]
                   [--private-key PRIVATE_KEY] [--num-documents NUM_DOCUMENTS]
                   [--regex REGEX] [--num-workers NUM_WORKERS]
                   [--max-num-errors MAX_NUM_ERRORS] [--ignore-harvest-time]
                   [--retry RETRY]

Harvest metadata from ARM.

optional arguments:
  -h, --help            show this help message and exit
  -v {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --verbosity {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Verbosity level of log file arm.log (default: INFO)
  --host HOST           Harvest records to this DataOne member node. (default:
                        localhost)
  --port PORT           DataOne member node SSL port. (default: 443)
  --certificate CERTIFICATE
                        Path to dataone client-side certificate. (default:
                        None)
  --private-key PRIVATE_KEY
                        Path to dataone host client-side key. (default: None)
  --num-documents NUM_DOCUMENTS
                        Limit number of documents retrieved to this number.
                        (default: -1)
  --regex REGEX         Limit documents retrieved to those whose URL match
                        this regular expression. (default: None)
  --num-workers NUM_WORKERS
                        Limit number of workers operating asynchronously to
                        this number. (default: 1)
  --max-num-errors MAX_NUM_ERRORS
                        Limit number of errors to this number. This number is
                        not exact, because if the number of asynchronous
                        workers is more than one, it is possible that the
                        threshold is passed simultaneously by more than one
                        worker. (default: 1)
  --ignore-harvest-time
                        Ignore the last harvest time. Use this switch to
                        attempt to harvest records that may have failed for
                        some reason on a recent harvest attempt. (default:
                        False)
  --retry RETRY         Retry a failed record this number of times. (default:
                        1)

Not supplying an argument to both the certificate and key arguments will
disable client side authentication.
```

## Example for Harvesting from Arctic Biodiversity Data Center

```shell
harvest-abds-ipt --port=8444 --max-num-errors=2
```

This sends harvested documents to a VM running locally with GMN.
There is an SSH tunnel already established for channeling SSL traffic
from port 8444 locally to 443 on the GMN VM.  There will be an expected
failure about 34 records into the processing that we wish to get past,
so an error threshold count is set to 2.  Out of 70 total datasets, 69 will be successfully processed.

The log of the harvest is as follows:


    2019-09-24 09:38:56,796 - datatone - INFO - Last harvest time:  1900-01-01 00:00:00+00:00
    2019-09-24 09:38:56,796 - datatone - INFO - Requesting sitemap document from http://geo.abds.is/ipt/rss.do
    2019-09-24 09:38:57,536 - datatone - INFO - Extracted 70 from the sitemap document.
    2019-09-24 09:38:57,536 - datatone - INFO - 0 records skipped due to last harvest time 1900-01-01 00:00:00+00:00 > lastmod times.
    2019-09-24 09:38:57,537 - datatone - INFO - Looking to process 70 records...
    2019-09-24 09:38:57,537 - datatone - INFO - sitemap_consumer[0] ==>  http://geo.abds.is/ipt/eml.do?r=arcod_2007p6, 2019-09-04 10:54:41+00:00:  job failure count = 0, queue size = 69
    2019-09-24 09:38:57,537 - datatone - INFO - Requesting http://geo.abds.is/ipt/eml.do?r=arcod_2007p6...
    2019-09-24 09:38:58,128 - datatone - INFO - Default validation failed with format ID http://www.isotc211.org/2005/gmd.
    2019-09-24 09:38:58,129 - datatone - INFO - Running validation against all format IDs.
    2019-09-24 09:38:58,257 - datatone - INFO - Validated against eml://ecoinformatics.org/eml-2.1.1
    2019-09-24 09:38:59,286 - datatone - INFO - CREATED object with SID: 59876921-fda6-4fd5-af5d-cba2a7152527 / PID: 59876921-fda6-4fd5-af5d-cba2a7152527/v1.3.
    2019-09-24 09:38:59,286 - datatone - INFO - Created a new object identified as 59876921-fda6-4fd5-af5d-cba2a7152527
    2019-09-24 09:38:59,286 - datatone - INFO - Successfully processed record: 59876921-fda6-4fd5-af5d-cba2a7152527
    2019-09-24 09:38:59,286 - datatone - INFO - sitemap_consumer[0] ==>  http://geo.abds.is/ipt/eml.do?r=as_zoo, 2019-09-03 14:14:08+00:00:  job failure count = 0, queue size = 68
    2019-09-24 09:38:59,286 - datatone - INFO - Requesting http://geo.abds.is/ipt/eml.do?r=as_zoo...
    2019-09-24 09:38:59,832 - datatone - INFO - CREATED object with SID: 451eb991-c1f4-479f-b1f8-7c1b4e8f9114 / PID: 451eb991-c1f4-479f-b1f8-7c1b4e8f9114/v1.2.
    2019-09-24 09:38:59,832 - datatone - INFO - Created a new object identified as 451eb991-c1f4-479f-b1f8-7c1b4e8f9114
    2019-09-24 09:38:59,832 - datatone - INFO - Successfully processed record: 451eb991-c1f4-479f-b1f8-7c1b4e8f9114
    2019-09-24 09:38:59,832 - datatone - INFO - sitemap_consumer[0] ==>  http://geo.abds.is/ipt/eml.do?r=dfo_amfd, 2019-08-29 12:55:15+00:00:  job failure count = 0, queue size = 67
    2019-09-24 09:38:59,832 - datatone - INFO - Requesting http://geo.abds.is/ipt/eml.do?r=dfo_amfd...
    2019-09-24 09:39:00,342 - datatone - INFO - CREATED object with SID: 40feadfa-94ea-4af3-90e1-5dffd0fb61df / PID: 40feadfa-94ea-4af3-90e1-5dffd0fb61df/v1.4.
    2019-09-24 09:39:00,342 - datatone - INFO - Created a new object identified as 40feadfa-94ea-4af3-90e1-5dffd0fb61df
    2019-09-24 09:39:00,342 - datatone - INFO - Successfully processed record: 40feadfa-94ea-4af3-90e1-5dffd0fb61df
    2019-09-24 09:39:00,343 - datatone - INFO - sitemap_consumer[0] ==>  http://geo.abds.is/ipt/eml.do?r=me2008g, 2019-08-26 14:17:03+00:00:  job failure count = 0, queue size = 66
    .
    .
    .
    .
    .
    .
    2019-09-24 09:39:16,416 - datatone - INFO - sitemap_consumer[0] ==>  http://geo.abds.is/ipt/eml.do?r=arc_2007f1, 2019-08-26 14:16:44+00:00:  job failure count = 0, queue size = 35
    2019-09-24 09:39:16,416 - datatone - INFO - Requesting http://geo.abds.is/ipt/eml.do?r=arc_2007f1...
    2019-09-24 09:39:16,834 - datatone - INFO - Default validation failed with format ID eml://ecoinformatics.org/eml-2.1.1.
    2019-09-24 09:39:16,836 - datatone - INFO - Running validation against all format IDs.
    2019-09-24 09:39:17,402 - datatone - ERROR - XML document does not validate. Errors and warnings:
      <string>: Line 6: Element '{eml://ecoinformatics.org/eml-2.1.1}eml': No matching global declaration available for the validation root.
    2019-09-24 09:39:17,414 - datatone - ERROR - Unable to process http://geo.abds.is/ipt/eml.do?r=arc_2007f1:  XML metadata validation failed.
    2019-09-24 09:39:17,414 - datatone - INFO - sitemap_consumer[0] ==>  http://geo.abds.is/ipt/eml.do?r=arcod_2006b2, 2019-08-26 14:16:43+00:00:  job failure count = 0, queue size = 34
    2019-09-24 09:39:17,414 - datatone - INFO - Requesting http://geo.abds.is/ipt/eml.do?r=arcod_2006b2...
    2019-09-24 09:39:17,961 - datatone - INFO - CREATED object with SID: 9bfd4499-050e-41b7-93a8-72d9e2490e21 / PID: 9bfd4499-050e-41b7-93a8-72d9e2490e21/v1.1.
    2019-09-24 09:39:17,961 - datatone - INFO - Created a new object identified as 9bfd4499-050e-41b7-93a8-72d9e2490e21
    2019-09-24 09:39:17,961 - datatone - INFO - Successfully processed record: 9bfd4499-050e-41b7-93a8-72d9e2490e21
    .
    .
    .
    2019-09-24 09:39:43,242 - datatone - INFO - sitemap_consumer[0] ==>  http://geo.abds.is/ipt/eml.do?r=arcod_2007b2, 2019-08-26 14:16:23+00:00:  job failure count = 0, queue size = 0
    2019-09-24 09:39:43,242 - datatone - INFO - Requesting http://geo.abds.is/ipt/eml.do?r=arcod_2007b2...
    2019-09-24 09:39:43,757 - datatone - INFO - CREATED object with SID: e2cde7e3-0b90-40ea-93ad-de06e6ed3a3c / PID: e2cde7e3-0b90-40ea-93ad-de06e6ed3a3c/v1.1.
    2019-09-24 09:39:43,757 - datatone - INFO - Created a new object identified as e2cde7e3-0b90-40ea-93ad-de06e6ed3a3c
    2019-09-24 09:39:43,757 - datatone - INFO - Successfully processed record: e2cde7e3-0b90-40ea-93ad-de06e6ed3a3c
    2019-09-24 09:39:43,757 - datatone - INFO - 
    .
    .
    .
    2019-09-24 09:39:43,757 - datatone - INFO - Job Summary
    2019-09-24 09:39:43,757 - datatone - INFO - ===========
    2019-09-24 09:39:43,758 - datatone - INFO - There were 69 new records.
    2019-09-24 09:39:43,758 - datatone - INFO - There were 0 updated records.
    2019-09-24 09:39:43,760 - datatone - INFO - Successfully processed 69 records.
    2019-09-24 09:39:43,765 - datatone - INFO - 
    .
    .
    .
    2019-09-24 09:39:43,768 - datatone - ERROR - Error summary:
                        count
    error                    
    XMLValidationError      1
    
    
    




# Example URLs for d1-check-site
1. No sitemap.

    $ d1-check-site http://104.236.112.76/demo/no_site_map/sitemap.xml

2. Two documents listed in sitemap, but one landing page is missing.

    $ d1-check-site http://104.236.112.76/demo/no_landing_page/sitemap.xml

3. A landing page has invalid JSON-LD.

    $ d1-check-site http://104.236.112.76/demo/invalid-json-ld/sitemap.xml

4. A landing page is missing its JSON-LD SCRIPT element.

    $ d1-check-site http://104.236.112.76/demo/missing-json-ld-script-element/sitemap.xml

5. A landing page is missing its JSON-LD ID.

    $ d1-check-site http://104.236.112.76/demo/missing-json-ld-id/sitemap.xml

6. Two documents listed, but one metadata XML document is missing.

    $ d1-check-site http://104.236.112.76/demo/missing-metadata-document/sitemap.xml

7. Two documents listed, but one metadata XML document has invalid XML.

    $ d1-check-site http://104.236.112.76/demo/metadata-document-has-invalid-xml/sitemap.xml

8. Two documents listed, but the first document does not validate according to any supported format IDs, which is different than having invalid XML.

    $ d1-check-site http://104.236.112.76/demo/metadata-document-does-not-validate/sitemap.xml

9. The sitemap is gzipped.

    $ d1-check-site http://104.236.112.76/demo/sitemap-is-gzipped/sitemap.xml.gz

10. The sitemap file is actually a sitemap index file, meaning there are multiple levels of sitemaps.

    $ d1-check-site http://104.236.112.76/demo/sitemap-url-is-sitemap-index-file/sitemap_index_file.xml

11. The sitemap file is text instead of XML.

    $ d1-check-site http://104.236.112.76/demo/sitemap-is-not-xml/sitemap.txt

12. Check only 5 documents.

    $ d1-check-site --num-documents=5 https://www.archive.arm.gov/metadata/adc/sitemap.xml