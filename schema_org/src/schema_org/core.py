"""
DATAONE SO core for multiple adaptors.
"""

# Standard library imports
import asyncio
import copy
from dataclasses import dataclass
import datetime as dt
import gzip
import hashlib
import io
import logging
import re
import sys
import time

# 3rd party library imports
import aiohttp
import dateutil.parser
import lxml.etree
import pandas as pd
import requests
import d1_scimeta.validate
import d1_common
import d1_common.types.dataoneTypes_v2_0 as v2
import d1_common.types.dataoneTypes_v2_0 as dataoneTypes

# Local imports
from .d1_client_manager import D1ClientManager
from .xml_validator import XMLValidator

SITEMAP_RETRIEVAL_FAILURE_MESSAGE = 'Failed to retrieve the site map.'
NO_JSON_LD_SCRIPT_ELEMENTS = "No JSON-LD <SCRIPT> elements were located."
SITEMAP_NOT_XML_MESSAGE = "The sitemap may not be XML."
SUCCESSFUL_INGEST_MESSAGE = "Successfully processed record"

ISO_NSMAP = {
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gml': 'http://www.opengis.net/gml/3.2',
    'xlink': 'http://www.w3.org/1999/xlink',
    'xs': 'http://www.w3.org/2001/XMLSchema'
}

SITEMAP_NS = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

# If an exception is one of these, then we may wish to try again.  Sometimes
ERROR_RETRY_CANDIDATES = (
    aiohttp.ClientPayloadError, aiohttp.ClientResponseError,
    asyncio.TimeoutError
)

_TOO_OLD_HARVEST_DATETIME = dateutil.parser.parse('1950-01-01T00:00:00Z')


@dataclass
class SlenderNodeJob(object):
    """
    Represents a job for processing a single document.

    Use dataclasses instead of a named tuple because named tuples are
    immutable and we want to keep track of the number of failures with any
    particular job.

    Attributes
    ----------
    url : str
        URL of either a landing page or metadata document
    identifier : str
        Usually a DOI, sometimes a UUID.  We often do not have this information
        when the job gets created.
    lastmod : datetime
        date when the document was last modified on the remote end
    num_failures : int
        Number of failures for this particular job so far.  If a job fails
        and the number of allowed failures per job is greater than 1, then we
        may want to try again.  Sometimes failures on the remote side may be
        sporadic.
    result : Exception or None
        None if the job succeeded, or the generated exception if the job
        failed.
    """
    url: str
    identifier: str
    lastmod: dt.datetime
    num_failures: int
    result: Exception


class SkipError(RuntimeError):
    """
    Raise this exception when there is reason to not even attempt to harvest
    a document with the GMN software.
    """
    pass


class RefusedToUpdateRecord(RuntimeError):
    """
    Raise this when we have a record whose metadata says we should not update
    it.  One reason seen was that a metadata timestamp regressed to an
    earlier date.
    """
    pass


class UnableToCreateNewGMNObject(RuntimeError):
    """
    Raise this when we have an identifier we have not seen before, but for
    some reason the GMN software cannot harvest it.
    """
    pass


class UnableToUpdateGmnRecord(RuntimeError):
    """
    Raise this when we have an identifier that we HAVE seen before, and the
    reported modification date indicates that we should update it, but for
    some reason the GMN software cannot update it.
    """
    pass


class XMLValidationError(RuntimeError):
    pass


class InvalidSitemapError(RuntimeError):
    pass


class XMLMetadataParsingError(RuntimeError):
    pass


class CoreHarvester(object):
    """
    Attributes
    ----------
    mn_host : str
        name of the gmn member node host
    client_mgs : object
        Handles direct communication with dataone host.
    {created,failed,rejected_updated}_count t: int
        Counters for the different ways that records are handled.  "failed" is
        different from "rejected" in the sense that this code knows why a
        rejection occurs.
    logger : logging.Logger
        All events are recorded by this object.
    _logstrings : io.StringIO
        If log_to_string is set to True, logs will also be stored here for
        later retrieval.
    _log_to_json : bool
        If true, log to JSON-compatible format.
    max_num_errors : int
        Abort if this threshold is reached.
    mn_base_url : str
        URL for contacting the dataONE host.
    num_documents : int
        Limit the number of documents to this number.  Less than zero
        means retrieve them all.
    num_records_processed : int
        Running total of number of records processed so far.
    num_workers : int
        Limit number of workers operating asynchronously to this number.  If
        1, then it is essentially synchronous.
    regex : str
        If not None, restrict documents to those that match this regular
        expression.
    sitemaps : list
        List of all sitemaps processed (only the leafs, though)
    sitemap_records : list
        List of the URLSET records (url and lastmod times) for all sitemaps.
    sitemap_url : str
        URL for XML site map.  This must be overridden for each custom client.
    session : requests.sessions.Session
        Makes all URL requests.
    sys_meta_dict : dict
        A dict containing node-specific system metadata properties that
        will apply to all science metadata documents loaded into GMN.  This
        should be specialized by each client.
    """
    SITEMAP_URL_PATH = './/sm:loc/text()'
    SITEMAP_LASTMOD_PATH = './/sm:lastmod/text()'
    SITEMAP_NAMESPACE = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    def __init__(self, host=None, port=None, certificate=None,
                 private_key=None, verbosity='INFO', id='none',
                 num_documents=-1, num_workers=1, max_num_errors=3,
                 regex=None, retry=0, ignore_harvest_time=False,
                 no_harvest=False, logger=None, sitemap_url=None):
        """
        Parameters
        ----------
        host, port : str, int
            This fully identifies the DataONE host and port number where we
            will be sending metadata records.
        certificate, private_key : str or path or None
            Paths to client side certificates.  None if no verification is
            desired.
        logger : logging.Logger
            Use this logger instead of the default.
        max_num_errors : int
            Abort if this threshold is reached.
        num_documents : int
            Limit the number of documents to this number.  Less than zero
            means retrieve them all.
        """
        self.mn_host = host
        self.setup_session(certificate, private_key)

        self.setup_logging(id, verbosity, logger=logger)

        self.mn_base_url = f'https://{host}:{port}/mn'
        self.sys_meta_dict = {
            'submitter': 'TBD',
            'rightsholder': 'TBD',
            'authoritativeMN': 'TBD',
            'originMN': 'TBD',

            # This will be determinted automatically.  No need to specialize
            # it.
            'formatId_custom': 'http://www.isotc211.org/2005/gmd'
        }

        self.client_mgr = D1ClientManager(self.mn_base_url,
                                          certificate, private_key,
                                          self.logger)

        self.job_records = []

        # Count the different ways that we update/create/skip records.  This
        # will be logged when we are finished.
        self.failed_count = 0
        self.updated_count = 0
        self.created_count = 0

        self.retry = retry

        self.num_documents = num_documents
        self.num_records_processed = 0

        self.num_workers = num_workers

        self.max_num_errors = max_num_errors

        self.regex = re.compile(regex) if regex is not None else None
        self.ignore_harvest_time = ignore_harvest_time
        self.no_harvest = no_harvest

        self.sitemap_url = sitemap_url
        self._sitemaps = []
        self._sitemap_records = []

        requests.packages.urllib3.disable_warnings()

    def get_sitemaps(self):
        """
        Return list of sitemaps (plural, in case the sitemap is nested).
        """
        return self._sitemaps

    def get_sitemaps_urlset(self):
        """
        Return list of landing page URLs and last modified times of the landing
        pages.

        Filter the items if no lastmod time was listed.  Replace the too-old
        time with None.
        """
        return [
            (item[0], None) if item[1] is _TOO_OLD_HARVEST_DATETIME else item
            for item in self._sitemap_records
        ]

    def setup_session(self, certificate, private_key):
        """
        Instantiate a requests session to help persist certain parameters
        across requests.

        See https://2.python-requests.org/en/master/user/advanced/ for further
        information.
        """

        self.session = requests.Session()

        # Setup the client side certificates if that makes sense.
        if certificate is None and private_key is None:
            self.session.verify = False
        else:
            self.session.cert = (certificate, private_key)

        # Always send these headers.
        self.session.headers = {
            'User-Agent': 'DataONE adapter for schema.org harvest',
            'From': 'jevans97@utk.edu'
        }

    def setup_logging(self, logid, verbosity, logger=None):
        """
        We will log both to STDOUT and to a file.

        Parameters
        ----------
        logid : str
            Use this to help name the physical log file.
        logger : logging.Logger
            Use this logger instead of the default.
        verbosity : str
            Level of logging verbosity.
        """
        if logger is not None:
            self.logger = logger
            return

        level = getattr(logging, verbosity)

        self.logger = logging.getLogger('datatone')
        self.logger.setLevel(level)

        # Do NOT change the formatting unless you review the
        # "extract_log_messages" method down below.
        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = logging.Formatter(format)

        # Use UTC, and fix the millisecond format so that javaScript can use
        # it
        formatter.default_msec_format = '%s.%03d'
        formatter.converter = time.gmtime

        # Log to file no matter what.
        #
        # I admit that the use of "delay" is only to prevent warnings being
        # issued during testing.
        fh = logging.FileHandler(f'{logid}.log', delay=True)
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        # Also log to stdout
        stream = logging.StreamHandler(sys.stdout)
        stream.setFormatter(formatter)
        self.logger.addHandler(stream)

    def generate_system_metadata(self, *,
                                 scimeta_bytes=None,
                                 native_identifier_sid=None,
                                 record_date=None,
                                 record_version=None):
        """
        This function generates a system metadata document for describing
        the science metadata record being loaded. Some of the fields,
        such as checksum and size, are based off the bytes of the science
        metadata object itself. Other system metadata fields are passed
        to D1ClientManager in a dict which is configured in the main
        adapter program.  Note that the checksum is assigned as an
        arbitrary version identifier to accommodate the source system's
        mutable content represented in the target system's immutable
        content standard.

        This is the default case.  It should be specialized by each slender
        nodes object.

        Parameters
        ----------
        scimeta_bytes :
            Bytes of the node's original metadata document.
        native_identifier_sid :
            Node's system identifier for this object, which becomes the series
            ID, or sid.
        record_date :
            Date metadata document was created/modified in the source
            system. Becomes dateUploaded.
        record_version : str
            Will be the pid.

        Returns
        -------
            A dict containing node-specific system metadata properties that
            will apply to all science metadata documents loaded into GMN.
        """
        sys_meta = v2.systemMetadata()
        sys_meta.seriesId = native_identifier_sid

        sys_meta.formatId = self.sys_meta_dict['formatId_custom']
        sys_meta.size = len(scimeta_bytes)

        digest = hashlib.md5(scimeta_bytes).hexdigest()
        sys_meta.checksum = dataoneTypes.checksum(digest)

        sys_meta.checksum.algorithm = 'MD5'

        if record_version is None:
            # only if we have nothing else.
            sys_meta.identifier = sys_meta.checksum.value()
        else:
            sys_meta.identifier = record_version

        sys_meta.dateUploaded = record_date
        sys_meta.dateSysMetadataModified = dt.datetime.now(dt.timezone.utc)
        sys_meta.rightsHolder = self.sys_meta_dict['rightsholder']
        sys_meta.submitter = self.sys_meta_dict['submitter']
        sys_meta.authoritativeMemberNode = self.sys_meta_dict['authoritativeMN']  # noqa:  E501
        sys_meta.originMemberNode = self.sys_meta_dict['originMN']
        sys_meta.accessPolicy = self.generate_public_access_policy()
        return sys_meta

    def generate_public_access_policy(self):
        """
        This function generates an access policy which is needed as
        part of system metadata for describing a science metadata object.
        In an adapter-based implementation, the ability to modify records
        is managed by the native repository, not GMN, and any changes
        in the native repository simple cascade down to GMN. This means
        it is unnecessary to set specific access policies for individual
        records. Therefore, a generic public read-only access policy
        is generated and assigned as part of system metadata to every
        record as it is loaded.
        """
        accessPolicy = v2.AccessPolicy()
        accessRule = v2.AccessRule()
        accessRule.subject.append(d1_common.const.SUBJECT_PUBLIC)
        permission = v2.Permission('write')
        accessRule.permission.append(permission)
        accessPolicy.append(accessRule)
        return accessPolicy

    def get_last_harvest_time(self):
        """
        Get the last time that a harvest was run on this node.

        Returns
        -------
        datetime of last harvest
        """
        if self.ignore_harvest_time:
            return None

        last_harvest_time_str = self.client_mgr.get_last_harvest_time()
        last_harvest_time = dateutil.parser.parse(last_harvest_time_str)

        self.logger.info(f'Last harvest time:  {last_harvest_time}')

        return last_harvest_time

    def summarize(self):
        """
        Produce a text summary for the logs about how the harvest went.
        """
        if self.no_harvest:
            return

        self.logger.info("\n\n")
        self.logger.info("Job Summary")
        self.logger.info("===========")
        self.logger.info(f"There were {self.created_count} new records.")
        self.logger.info(f"There were {self.updated_count} updated records.")

        self.summarize_job_records()

    def summarize_job_records(self):
        """
        Summarize the job record queue.  Keep this factored out of the
        summarize routine for the purpose of testing.
        """
        # Create a pandas dataframe out of the job results.
        columns = ['URL', 'Identifier', 'NumFailures', 'Result']
        records = [
            (job.url, job.identifier, job.num_failures, job.result)
            for job in self.job_records
        ]
        df = pd.DataFrame.from_records(records, columns=columns)

        # The rows with None in the Results column are successes.  Anything
        # else in there should be an Exception object.
        msg = f"Successfully processed {df.Result.isnull().sum()} records."
        self.logger.info(msg)

        # Restrict to the job failures.
        df = df.dropna(subset=['Result'])
        if len(df) == 0:
            # If no errors, then nothing more to do.
            return

        # Split the exceptions into two parts, the exception name and the
        # exception message.
        fcn = lambda x: repr(x).split('(')[0]  # noqa:  E371
        df = df.assign(error=lambda df: df.Result.apply(fcn))
        columns = ['URL', 'Identifier', 'NumFailures', 'Result']
        df_error = df.drop(columns, axis='columns')
        df_error['count'] = 1
        summary = df_error.groupby('error').sum()

        self.logger.info("\n\n")

        msg = f"Error summary:\n\n{summary}\n\n"
        self.logger.error(msg)

    async def shutdown(self):
        """
        Clean up tasks tied to the service's shutdown.
        """
        msg = 'Shutting down...'
        self.logger.info(msg)

        tasks = [
            t for t in asyncio.all_tasks() if t is not asyncio.current_task()
        ]
        msg = f"Cancelling {len(tasks)} outstanding tasks."
        self.logger.info(msg)
        [task.cancel() for task in tasks]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def harvest_document(self, sid, pid, doc, record_date):
        """
        Check if the member node has seen the document before and decide how to
        harvest it (or not) accordingly.

        Parameters
        ----------
        sid : str
            Handle used to identify objects uniquely.  Also known as the
            series identifier.
        pid : str
            Record version.
        doc : bytes
            serialized version of XML metadata document
        record_date : datetime obj
            Last document modification time according to the site map.
        """
        self.logger.debug(f'harvest_document:  {sid}')

        # Re-seriealize to bytes.
        docbytes = lxml.etree.tostring(doc, pretty_print=True,
                                       encoding='utf-8', standalone=True)

        kwargs = {
            'scimeta_bytes': docbytes,
            'native_identifier_sid': sid,
            'record_date': record_date,
            'record_version': pid
        }
        sys_metadata = self.generate_system_metadata(**kwargs)

        exists_dict = self.client_mgr.check_if_identifier_exists(sid)

        if (
            exists_dict['outcome'] == 'yes'
            and exists_dict['record_date'] != record_date
        ):
            current_sid = exists_dict['current_version_id']
            await self.check_if_can_be_updated(docbytes, sid, current_sid)

            # the outcome of exists_dict determines how to
            # handle the record.  if identifier exists in GMN but
            # record date is different, this truly is an update so
            # call update method.
            kwargs = {
                'sci_metadata_bytes': docbytes,
                'native_identifier_sid': sid,
                'record_date': record_date,
                'old_version_pid': exists_dict['current_version_id'],
                'system_metadata': sys_metadata
            }
            if self.client_mgr.update_science_metadata(**kwargs):
                self.updated_count += 1
                self.logger.info(f'Updated {sid}.')
            else:
                raise UnableToUpdateGmnRecord(f'Unable to update {sid}.')

        elif (
            exists_dict['outcome'] == 'yes'
            and exists_dict['record_date'] == record_date
        ):
            # if identifier exists but record date is the same, it's not really
            # an update. So skip it and move on.
            msg = (
                f'Skipping {sid}, '
                f'it already exists and has the same record date {record_date}'
            )
            raise SkipError(msg)

        elif exists_dict['outcome'] == 'failed':
            # if check failed for some reason, d1_client_manager would have
            # logged the error so just skip.
            msg = (
                f'The existance check for {sid} failed.  Is this '
                f'logged anywhere?'
            )
            self.logger.warning(msg)

        elif exists_dict['outcome'] == 'no':
            # If this identifer is not already found in GMN in any way, then
            # create a new object in GMN
            kwargs = {
                'sci_metadata_bytes': docbytes,
                'native_identifier_sid': sid,
                'record_date': record_date,
                'system_metadata': sys_metadata
            }
            if self.client_mgr.load_science_metadata(**kwargs):
                # track number of successfully created new objects
                self.created_count += 1

                msg = f'Created a new object identified as {sid}'
                self.logger.info(msg)

            else:
                msg = (
                    f'Unable to create new object identified as {sid}.'
                )
                raise UnableToCreateNewGMNObject(msg)

    async def check_if_can_be_updated(self, new_doc_bytes, doi, existing_sid):
        """
        We have an existing document in the system and have been give a
        proposed update document.  We need to decide if an update is warranted.

        The tie-breakers are:

            i)  the value of the MD_ProgressCode.
            ii) the value of the dateStamp.

        We can currently only do this check when the format ID is the default.
        """
        if self.sys_meta_dict['formatId_custom'] != 'http://www.isotc211.org/2005/gmd':  # noqa:  E501
            return True

        new_doc = lxml.etree.parse(io.BytesIO(new_doc_bytes))

        url = f"{self.mn_base_url}/v2/object/{existing_sid}"

        # Get the existing document.
        content, _ = await self.retrieve_url(url, headers={'Accept': 'text/xml'})  # noqa : E501

        old_doc = lxml.etree.parse(io.BytesIO(content))

        # Get the progress code
        parts = [
            'gmd:identificationInfo',
            'gmd:MD_DataIdentification',
            'gmd:status',
            'gmd:MD_ProgressCode',
            'text()'
        ]
        path = '/'.join(parts)
        new_progress_code = new_doc.xpath(path, namespaces=ISO_NSMAP)[0]
        old_progress_code = old_doc.xpath(path, namespaces=ISO_NSMAP)[0]  # noqa:  F841

        # Get the metadata timestamp.  There are two possible paths.
        path = (
            'gmd:dateStamp/gco:Date/text()'
            '|'
            'gmd:dateStamp/gco:DateTime/text()'
        )
        s = new_doc.xpath(path, namespaces=ISO_NSMAP)[0]
        new_timestamp = dateutil.parser.parse(s)
        s = old_doc.xpath(path, namespaces=ISO_NSMAP)[0]
        old_timestamp = dateutil.parser.parse(s)

        if (
            new_progress_code.lower() in ['complete', 'completed']
            and old_progress_code.lower() not in ['complete', 'completed']
        ):
            # Yes, we should update.  The new document is finished while the
            # old document is not.
            return
        elif (
            new_progress_code.lower() in ['complete', 'completed']
            and old_progress_code.lower() in ['complete', 'completed']
            and new_timestamp > old_timestamp
        ):
            # We have a tie between the progress codes, but the proposed
            # update document has a newer timestamp.
            return
        else:
            msg = (
                f"The existing document identified by {doi} with SID "
                f"{existing_sid} has an MD_ProgressCode of "
                f"\"{old_progress_code}\" and a metadata timestamp of "
                f"{old_timestamp} while the proposed updating "
                f"document has MD_ProgressCode \"{new_progress_code}\" and a "
                f"metadata timestamp of {new_timestamp}."
            )
            raise RefusedToUpdateRecord(msg)

    def is_sitemap_index_file(self, doc):
        """
        Answer the question as to whether the document found at the other end
        of the sitemap URL is a sitemap index file - i.e. it references other
        sitemaps - or if it is a sitemap leaf.

        Parameters
        ----------
        doc : ElementTree
            the sitemap XML document loaded into an ElementTree object

        Returns
        -------
        True or False, whether or not the document is a sitemap index file.
        """

        elts = doc.xpath('sm:sitemap', namespaces=SITEMAP_NS)
        if len(elts) > 0:
            return True
        else:
            return False

    def extract_records_from_sitemap(self, doc):
        """
        Extract all the URLs and lastmod times from an XML sitemap.

        Parameters
        ----------
        doc : ElementTree
            the sitemap XML document loaded into an ElementTree object

        Returns
        -------
        List of tuples, each consisting of a URL for a metadata document and
        its associated last modification time.
        """
        urls = doc.xpath(self.SITEMAP_URL_PATH,
                         namespaces=self.SITEMAP_NAMESPACE)

        # If the URLs do not begin with 'http', then they may be relative?
        # If so, tack the sitemap URL onto them.
        urls = [
            f"{self.sitemap_url}/{url}" if not url.startswith('http') else url
            for url in urls
        ]

        lastmods = doc.xpath(self.SITEMAP_LASTMOD_PATH,
                             namespaces=self.SITEMAP_NAMESPACE)
        if len(lastmods) == 0:
            # Sometimes a sitemap has no <lastmod> items at all.  That's ok.
            # Use a datetime that we know is too old to be valid.
            lastmods = [_TOO_OLD_HARVEST_DATETIME for url in urls]
        else:
            # Parse the last modification times.  It is possible that the dates
            # have no timezone information in them, so we will assume that it
            # is UTC.
            lastmods = [dateutil.parser.parse(item) for item in lastmods]
            UTC = dateutil.tz.gettz("UTC")
            lastmods = [
                dateitem.replace(tzinfo=dateitem.tzinfo or UTC)
                for dateitem in lastmods
            ]

        records = [(url, lastmod) for url, lastmod in zip(urls, lastmods)]

        msg = f"Extracted {len(urls)} from the sitemap document."
        self.logger.info(msg)
        return records

    def post_process_sitemap_records(self, records, last_harvest_time):
        """
        Prune the sitemap records for various reasons.  These might include:

            i)
                pruning any records that are older than the last harvest time
                IFF we are not directed to ignore the last harvest time
            ii)
                pruning records that do not match a regex IFF we are directed
                to use a regex
            iii)
                pruning records if we are limiting the number of documents that
                we are willing to process

        Parameters
        ----------
        records : list
            Each item in the list is composed of a URL and a last modification
            date.
        """
        # If we do not wish to ignore the last harvest time, then only those
        # records in the sitemap that are newer than the last harvest time will
        # pass through.
        nrecs = len(records)
        if not self.ignore_harvest_time:
            records = [
                (url, lastmod) for url, lastmod in records
                if lastmod > last_harvest_time
            ]

            nskipped = nrecs - len(records)
            msg = (
                f"{nskipped} records skipped due to last harvest time "
                f"{last_harvest_time} > lastmod times."
            )
            self.logger.info(msg)

        # If a regex was specified, filter out any records that do not match.
        if self.regex is not None:
            nrecs = len(records)
            records = [
                (url, lastmod) for url, lastmod in records
                if self.regex.search(url)
            ]
            num_skipped = nrecs - len(records)
            msg = f"{num_skipped} records skipped due to regex restriction."
            self.logger.info(msg)

        # Check that we do not exceed the maximum number of documents.
        self.num_records_processed += len(records)
        if (
            self.num_records_processed > self.num_documents
            and self.num_documents > -1
        ):
            diff = self.num_records_processed - self.num_documents
            records = records[:-diff]

        msg = f"Looking to process {len(records)} records..."
        self.logger.info(msg)
        return records

    async def retrieve_url(self, url, headers=None):
        """
        Return the contents pointed to by a URL.

        Parameters
        ----------
        url : str
            URL of either an HTML document or an XML metadata document
        headers : dict
            Optional headers to supply with the retrieval.

        Returns
        -------
        Binary contents of the body of the response object, response headers
        """
        self.logger.info(f'Retrieving URL {url}')

        headers = {
            'User-Agent': 'DataONE adapter for schema.org harvest',
            'From': 'jevans97@utk.edu'
        }
        connector = aiohttp.TCPConnector(ssl=False)

        async with aiohttp.ClientSession(headers=headers,
                                         connector=connector) as session:

            async with session.get(url) as response:

                response.raise_for_status()

                return await response.read(), response.headers

    def check_xml_headers(self, headers):
        """
        Check the headers returned by the sitemap request response.

        Parameters
        ----------
        headers : dict
            HTTP response headers
        """
        self.logger.debug('Checking XML headers...')
        exp_headers = [
            'text/xml',
            'text/xml;charset=utf-8',
            'application/x-gzip',
            'application/xml'
        ]
        if headers['Content-Type'].lower() not in exp_headers:
            msg = f"get_sitemap_document: headers are {headers}"
            self.logger.debug(msg)
            self.logger.warning(SITEMAP_NOT_XML_MESSAGE)

    async def run(self):

        self.logger.debug(f'run:  num_workers = {self.num_workers}')
        last_harvest_time = self.get_last_harvest_time()

        try:
            await self.process_sitemap(self.sitemap_url, last_harvest_time)
        except Exception as e:
            self.logger.error(repr(e))

        self.summarize()

    async def retrieve_metadata_document(self, metadata_url):
        """
        Retrieve the remote metadata document and make any necessary
        transformations on it.

        Parameters
        ----------
        metadata_url : str
            URL of remote metadata document
        identifier : str
            ID from JSON-LD description

        Returns
        -------
        The ElementTree document.
        """
        msg = f'requesting {metadata_url}'
        self.logger.info(msg)
        # Retrieve the metadata document.
        content, _ = await self.retrieve_url(metadata_url)

        try:
            doc = lxml.etree.parse(io.BytesIO(content))
        except Exception as e:
            msg = (
                f"Unable to parse the metadata document at {metadata_url}:  "
                f"{e}."
            )
            raise XMLMetadataParsingError(msg)

        self.logger.debug('Got the metadata document')
        return doc

    async def consume_sitemap(self, idx, sitemap_queue):
        """
        In a producer/consumer paradigm, here we are consuming work items
        from the sitemap.

        Parameters
        ----------
        idx:  int
            The only purpose for this is to identify the consumer in the logs.
        sitemap_queue : asyncio.Queue
            Holds jobs associated with the sitemap.  Each job includes, among
            other things, a URL and a modification time.
        """
        while True:
            try:
                job = await sitemap_queue.get()
                msg = (
                    f"sitemap_consumer[{idx}] ==>  {job.url}, "
                    f"{job.lastmod}:  "
                    f"job failure count = {job.num_failures}, "
                    f"queue size = {sitemap_queue.qsize()}"
                )
                self.logger.info(msg)

                await self.process_job(job)

            except asyncio.CancelledError:
                # This is ok, it is a signal that we are done.  Our custom
                # shutdown process will raise this exception.  Trying to
                # retrieve from an empty queue will also raise the exception.
                # Just break out of this loop and the consumer task will then
                # be over.
                self.logger.debug('CancelledError')
                break

            except SkipError as e:
                # For whatever reason, we cannot proceed with the current job,
                # but we do not count the situation as an "error".  All we do
                # is tally the issue.
                job.result = e
                self.job_records.append(copy.copy(job))
                msg = f"Unable to process {job.url}:  {e}"
                self.logger.warning(msg)

            except Exception as e:
                # There was a genuine error situation.  Tally the issue AND
                # take other action as needed.
                job.result = e

                self.job_records.append(copy.copy(job))

                msg = f"Unable to process {job.url}:  {e}"
                self.logger.error(msg)

                self.failed_count += 1
                if self.failed_count == self.max_num_errors:
                    self.logger.warning("Error threshold reached.")
                    await self.shutdown()

                if job.num_failures < self.retry:
                    # If we are instructed to retry a job in case of certain
                    # errors (a network glitch, maybe?), we put the job back
                    # onto the work queue, but increment the count so that we
                    # don't get caught in an infinite loop retrying a bad
                    # URL or some such thing.
                    if isinstance(e, ERROR_RETRY_CANDIDATES):
                        self.logger.info(f"Throwing {job.url} back on queue")
                        job.num_failures += 1
                        sitemap_queue.put_nowait(job)

            else:
                # The job was successful, so just tally the result.
                job.result = None
                self.job_records.append(copy.copy(job))

                msg = (
                        f"sitemap_consumer[{idx}]:  "
                        f"{SUCCESSFUL_INGEST_MESSAGE}: {job.identifier}"
                )
                self.logger.debug(msg)

                msg = f"{SUCCESSFUL_INGEST_MESSAGE}: {job.identifier}"
                self.logger.info(msg)

            sitemap_queue.task_done()

    async def process_job(self, job):
        """
        Now that we have the record, validate and harvest it.

        Parameters
        ----------
        job : SlenderNodeJob
            Record containing at least the following attributes: landing page
            URL, last document modification time according to the site map.
        """
        self.logger.debug(f'process_job:  starting')

        series_id, version_id, doc = await self.retrieve_record(job.url)

        job.identifier = series_id
        self.validate_document(doc)

        await self.harvest_document(series_id, version_id, doc, job.lastmod)

        self.logger.debug(f'process_job:  finished')

    def validate_document(self, doc):
        """
        Verify that the format ID we have for the document is correct.

        Parameters
        ----------
        doc : bytes
            serialized version of XML metadata document
        """
        format_id = self.sys_meta_dict['formatId_custom']
        try:
            d1_scimeta.validate.assert_valid(format_id, doc)
        except Exception:
            # Ok, so it did not validate against the default id.  Try to
            # figure out another format id that works.
            msg = f"Default validation failed with format ID {format_id}."
            self.logger.info(msg)

            validator = XMLValidator(logger=self.logger)
            format_id = validator.validate(doc)
            if format_id is None:
                raise XMLValidationError('XML metadata validation failed.')
            else:
                # Reset the format ID to the one that worked.
                self.sys_meta_dict['formatId_custom'] = format_id

    async def retrieve_record(self, document_url):
        """
        Parameters
        ----------
        document_url : str
            URL for a remote document, could be a landing page, could be an
            XML document

        Returns
        -------
        identifier : str
            Ideally this is a DOI, but here it is a UUID.
        doc : ElementTree
            Metadata document
        """
        raise NotImplementedError('must implement retrieve_record in sub class')  # noqa:  E501

    async def process_sitemap(self, sitemap_url, last_harvest):
        """
        Determine if the sitemap (or RSS feed or whatever) is an index file
        or whether it is a single document.  If an index file, we need to
        descend recursively into it.

        Parameters
        ----------
        sitemap_url : str
            URL for a sitemap or sitemap index file
        last_harvest : datetime
            According to the MN, this is the last time we, uh, harvested any
            document.
        """
        msg = f"process_sitemap: {sitemap_url}, {last_harvest}"
        self.logger.debug(msg)

        doc = await self.get_sitemap_document(sitemap_url)
        if self.is_sitemap_index_file(doc):

            msg = "process_sitemap:  This is a sitemap index file."
            self.logger.debug(msg)

            path = 'sm:sitemap/sm:loc/text()'
            sitemap_urls = doc.xpath(path, namespaces=SITEMAP_NS)
            for sitemap_url in sitemap_urls:
                await self.process_sitemap(sitemap_url, last_harvest)

        else:

            self.logger.debug("process_sitemap:  This is a sitemap leaf.")
            self._sitemaps.append(sitemap_url)
            await self.process_sitemap_leaf(doc, last_harvest)

    async def get_sitemap_document(self, sitemap_url):
        """
        Retrieve a remote sitemap document.

        Parameters
        ---------
        sitemap_url : str
            URL for a sitemap or sitemap index file.
        """
        self.logger.info(f'Requesting sitemap document from {sitemap_url}')

        try:
            content, headers = await self.retrieve_url(sitemap_url)
            self.check_xml_headers(headers)
        except Exception as e:
            msg = f"{SITEMAP_RETRIEVAL_FAILURE_MESSAGE} due to {repr(e)}"
            self.logger.error(msg)
            raise

        try:
            doc = lxml.etree.parse(io.BytesIO(content))
        except lxml.etree.XMLSyntaxError as e:
            msg1 = str(e)

            try:
                # Gzipped XML can cause an XMLSyntaxError, so try again.
                doc = lxml.etree.parse(io.BytesIO(gzip.decompress(content)))
            except OSError:
                # Must not have been gzipped.
                # TODO:  Is there some other possibility here?
                msg = (
                    f"XMLSyntaxError:  sitemap document at {sitemap_url}: "
                    f"{msg1}"
                )
                self.logger.error(msg)

                msg = (
                    f'Unable to process the sitemap retrieved from '
                    f'{sitemap_url}.'
                )
                raise InvalidSitemapError(msg)

        return doc

    async def process_sitemap_leaf(self, doc, last_harvest):
        """
        We are at a sitemap leaf, i.e. the sitemap does not reference other
        sitemaps.  This is where we can retrieve landing pages instead of
        other sitemaps.

        Parameters
        ----------
        doc : ElementTree object
            Describes the sitemap leaf.
        last_harvest : datetime
            According to the MN, this is the last time we, uh, harvested any
            document.
        """
        self.logger.debug(f'process_sitemap_leaf:')

        records = self.extract_records_from_sitemap(doc)
        records = self.post_process_sitemap_records(records, last_harvest)

        self._sitemap_records.extend(records)

        if self.no_harvest:
            return

        sitemap_queue = asyncio.Queue()

        for url, lastmod_time in records:
            job = SlenderNodeJob(url, '', lastmod_time, 0, None)
            sitemap_queue.put_nowait(job)

        # Create the worker tasks to consume the URLs
        tasks = []
        for j in range(self.num_workers):
            msg = (
                f'process_sitemap_leaf: create task for sitemap_consumer[{j}]'
            )
            self.logger.debug(msg)
            task = asyncio.create_task(self.consume_sitemap(j, sitemap_queue))
            tasks.append(task)
        await sitemap_queue.join()

        # Cancel any remaining tasks.
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
