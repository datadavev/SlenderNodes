===============
Sitemap Checker
===============

----
Help
----
The sitemap checker is a command line utility that may be used to determine the viability of a proposed member node's site map and the validity of its metadata documents.  The sitemap checker is essentially a web crawler that will start at a given URL for a sitemap and then retrieve and validate each metadata document listed.  Most of the optional arguments are only useful for debugging purposes::

    usage: d1-check-site [-h] [-v {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
                         [--num-documents NUM_DOCUMENTS] [--regex REGEX]
                         [--num-workers NUM_WORKERS]
                         [--max-num-errors MAX_NUM_ERRORS]
                         sitemap_url
    
    Crawl a sitemap, check metadata for validity.
    
    positional arguments:
      sitemap_url           URL of site map
    
    optional arguments:
      -h, --help            show this help message and exit
      -v {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --verbosity {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                            Verbosity level of log file site-checker.log (default:
                            INFO)
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


-------
Example
-------

Limit the number of documents to be processed from
`ARM <https://www.ornl.gov/group/arm-data-science-and-integration>`_
(Atmospheric Radiation Measurement Group)
to just 3.  The total number of documents
found in the sitemap is 193, so this results in a fairly fast operation::

    $ d1-check-site --num-documents=3 https://www.archive.arm.gov/metadata/adc/sitemap.xml
    2019-12-09 14:56:20.846 - datatone - INFO - Requesting sitemap document from https://www.archive.arm.gov/metadata/adc/sitemap.xml
    2019-12-09 14:56:21.213 - datatone - INFO - Extracted 193 from the sitemap document.
    2019-12-09 14:56:21.214 - datatone - INFO - 0 records skipped due to last harvest time 1900-01-01 00:00:00+00:00 > lastmod times.
    2019-12-09 14:56:21.214 - datatone - INFO - Looking to process 3 records...
    2019-12-09 14:56:21.215 - datatone - INFO - last mod = 2019-11-25 00:00:00+00:00:  num failures so far = 0, queue size = 2
    2019-12-09 14:56:21.215 - datatone - INFO - Retrieving landing page https://www.archive.arm.gov/metadata/adc/html/microbasepiavg.html
    2019-12-09 14:56:22.734 - datatone - INFO - Retrieving XML metadata document https://www.archive.arm.gov/metadata/adc/xml/microbasepiavg.xml
    2019-12-09 14:56:22.924 - datatone - INFO - Successfully processed record: doi:10.5439/1095339
    2019-12-09 14:56:22.924 - datatone - INFO - last mod = 2019-11-25 00:00:00+00:00:  num failures so far = 0, queue size = 1
    2019-12-09 14:56:22.924 - datatone - INFO - Retrieving landing page https://www.archive.arm.gov/metadata/adc/html/wsicloudspec.html
    2019-12-09 14:56:23.337 - datatone - INFO - Retrieving XML metadata document https://www.archive.arm.gov/metadata/adc/xml/wsicloudspec.xml
    2019-12-09 14:56:23.526 - datatone - INFO - Successfully processed record: doi:10.5439/1027764
    2019-12-09 14:56:23.527 - datatone - INFO - last mod = 2019-11-25 00:00:00+00:00:  num failures so far = 0, queue size = 0
    2019-12-09 14:56:23.527 - datatone - INFO - Retrieving landing page https://www.archive.arm.gov/metadata/adc/html/30ecor.html
    2019-12-09 14:56:23.954 - datatone - INFO - Retrieving XML metadata document https://www.archive.arm.gov/metadata/adc/xml/30ecor.xml
    2019-12-09 14:56:24.145 - datatone - INFO - Successfully processed record: doi:10.5439/1025039
    2019-12-09 14:56:24.146 - datatone - INFO -
    
    
    2019-12-09 14:56:24.146 - datatone - INFO - Job Summary
    2019-12-09 14:56:24.146 - datatone - INFO - ===========
    2019-12-09 14:56:24.148 - datatone - INFO - Successfully processed 3 records.
