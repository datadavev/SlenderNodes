# Standard library imports
import asyncio
import copy
import datetime as dt
try:
    import importlib.resources as ir
except ImportError:  # pragma:  nocover
    import importlib_resources as ir
import io
import json
import logging
import re
import string
from unittest.mock import patch

# 3rd party library imports
import dateutil.parser
import lxml.etree
import numpy as np
from pythonjsonlogger import jsonlogger

# local imports
from schema_org.core import CoreHarvester, SlenderNodeJob, SkipError
from .test_common import TestCommon


class TestSuite(TestCommon):

    @patch('schema_org.core.logging.getLogger')
    def test_restrict_to_2_items_from_sitemap(self, mock_logger):
        """
        SCENARIO:  The sitemap lists 3 documents, but we have specified that
        only 2 are to be processed.

        EXPECTED RESULT:  The list of documents retrieve has length 2.
        """

        harvester = CoreHarvester(num_documents=2)

        content = ir.read_binary('tests.data.ieda', 'sitemap3.xml')
        doc = lxml.etree.parse(io.BytesIO(content))
        last_harvest = dateutil.parser.parse('1900-01-01T00:00:00Z')

        records = harvester.extract_records_from_sitemap(doc)
        records = harvester.post_process_sitemap_records(records, last_harvest)

        self.assertEqual(len(records), 2)

    @patch('schema_org.core.logging.getLogger')
    def test_sitemap_num_docs_restriction_does_not_apply(self, mock_logger):
        """
        SCENARIO:  The sitemap lists 3 documents, but we have specified that
        4 are to be processed.

        EXPECTED RESULT:  The list of documents retrieve has length 3.  The
        setting of 4 has no effect.
        """

        harvester = CoreHarvester(num_documents=4)

        content = ir.read_binary('tests.data.ieda', 'sitemap3.xml')
        doc = lxml.etree.parse(io.BytesIO(content))
        last_harvest = dateutil.parser.parse('1900-01-01T00:00:00Z')

        records = harvester.extract_records_from_sitemap(doc)
        records = harvester.post_process_sitemap_records(records, last_harvest)
        self.assertEqual(len(records), 3)

    def test_no_lastmod_time_in_sitemap_leaf(self):
        """
        SCENARIO:  A sitemap leaf XML file has <loc> entries, but no <lastmod>
        entries.  In this case, we should look to the lastModified field in the
        JSON-LD for guidance.

        CUAHSI has no <lastmod> entries in their sitemap.

        EXPECTED RESULT:  The entries in the sitemap are NOT skipped.
        """
        content = ir.read_binary('tests.data.cuahsi', 'sitemap-pages.xml')
        doc = lxml.etree.parse(io.BytesIO(content))

        last_harvest_time_str = '1900-01-01T00:00:00Z'
        last_harvest_time = dateutil.parser.parse(last_harvest_time_str)

        obj = CoreHarvester()

        with self.assertLogs(logger=obj.logger, level='DEBUG'):
            records = obj.extract_records_from_sitemap(doc)
            records = obj.post_process_sitemap_records(records,
                                                       last_harvest_time)
        self.assertEqual(len(records), 3)

    def test_sitemap_when_regex_applied(self):
        """
        SCENARIO:  The sitemap lists 3 documents, but two of them are to be
        excluded via regular expression.

        EXPECTED RESULT:  Only two records are extracted from the sitemap.
        """
        xmlstr = b"""<?xml version="1.0" encoding="utf-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url>
            <loc>http://get.iedadata.org/metadata/iso/609246</loc>
            <lastmod>2018-06-21T22:05:27-04:00</lastmod>
          </url>
          <url>
            <loc>http://get.iedadata.org/metadata/iso/600048</loc>
            <lastmod>2018-06-21T22:05:24-04:00</lastmod>
          </url>
          <url>
            <loc>http://get.iedadata.org/metadata/iso/609469</loc>
            <lastmod>2018-06-21T22:05:27-04:00</lastmod>
          </url>
        </urlset>
        """
        doc = lxml.etree.parse(io.BytesIO(xmlstr))

        last_harvest_time_str = '1900-01-01T00:00:00Z'
        last_harvest_time = dateutil.parser.parse(last_harvest_time_str)

        regex = re.compile('609469')

        obj = CoreHarvester(regex=regex)

        with self.assertLogs(logger=obj.logger, level='DEBUG'):
            records = obj.extract_records_from_sitemap(doc)
            records = obj.post_process_sitemap_records(records,
                                                       last_harvest_time)
        self.assertEqual(len(records), 1)

    def test_summary_when_no_jobs_attempted(self):
        """
        SCENARIO:  No documents are suitable for harvesting.  This could happen
        if, say, a sitemap is empty.

        EXPECTED RESULT:  The summary is states that no jobs were processed.
        """
        harvester = CoreHarvester()
        harvester.job_records = []

        with self.assertLogs(logger=harvester.logger, level='INFO') as cm:
            harvester.summarize_job_records()

            messages = [
                "Successfully processed 0 records.",
            ]
            self.assertInfoLogMessage(cm.output, messages)
            self.assertLogLevelCallCount(cm.output, level='INFO', n=1)

    def _create_jobs(self, n=100, result=None):
        """
        Helper routine for construct a fake set of job records.
        """

        n = 100
        urls = [
            ''.join(np.random.choice(list(string.ascii_letters), 10))
            for _ in range(n)
        ]
        identifiers = [
            ''.join(np.random.choice(list(string.ascii_letters), 10))
            for _ in range(n)
        ]
        lastmods = [dt.datetime(1900, 1, 1) for _ in range(n)]
        num_failures = [0 for _ in range(n)]
        results = [result for _ in range(n)]

        jobs = [
            SlenderNodeJob(url, identifier, time, num_failures, result)
            for url, identifier, time, num_failures, result
            in zip(urls, identifiers, lastmods, num_failures, results)
        ]

        return jobs

    def test_summary_when_all_jobs_successful(self):
        """
        SCENARIO:  All jobs were successfully processed.

        EXPECTED RESULT:  The summary states that all jobs were processed.
        """
        harvester = CoreHarvester()
        jobs = self._create_jobs(n=100)
        harvester.job_records = jobs

        with self.assertLogs(logger=harvester.logger, level='INFO') as cm:
            harvester.summarize_job_records()

            messages = [
                "Successfully processed 100 records.",
            ]
            self.assertInfoLogMessage(cm.output, messages)
            self.assertLogLevelCallCount(cm.output, level='INFO', n=1)

    def test_summary_when_no_jobs_successful(self):
        """
        SCENARIO:  Jobs are attempted, but all fail.

        EXPECTED RESULT:  The summary states that no jobs were successful and
        there is a summary of the errors.
        """
        harvester = CoreHarvester()

        result = ZeroDivisionError('this would never actually happen')
        jobs = self._create_jobs(n=100, result=result)
        harvester.job_records = jobs

        with self.assertLogs(logger=harvester.logger, level='INFO') as cm:
            harvester.summarize_job_records()

            messages = [
                "Successfully processed 0 records.",
            ]
            self.assertInfoLogMessage(cm.output, messages)

            # The output here is a bit hard to construct, so just get the
            # pieces right.
            message = """
            Error summary:

                               count
            error
            ZeroDivisionError    100
            """
            messages = [m.strip() for m in message.split('\n')]
            self.assertErrorLogMessage(cm.output, messages)

    def test_summary_when_only_one_of_many_jobs_successful(self):
        """
        SCENARIO:  Jobs are attempted, but all but one fail.

        EXPECTED RESULT:  The summary states that no jobs were successful and
        there is a summary of the errors.
        """
        harvester = CoreHarvester()

        result = ZeroDivisionError('this would never actually happen')
        jobs = self._create_jobs(n=100, result=result)

        # Pick one job and make it successful
        jobs[55].result = None

        harvester.job_records = jobs

        with self.assertLogs(logger=harvester.logger, level='INFO') as cm:
            harvester.summarize_job_records()

            messages = [
                "Successfully processed 1 records.",
            ]
            self.assertInfoLogMessage(cm.output, messages)

            # The output here is a bit hard to construct, so just get the
            # pieces right.
            message = """
            Error summary:

                               count
            error
            ZeroDivisionError    99
            """
            messages = message.split()
            self.assertErrorLogMessage(cm.output, messages)

    def test_summary_when_one_job_succeeds_on_retry(self):
        """
        SCENARIO:  All jobs are eventually successful.  One fails on its
        first try, but succeeds upon retry.

        EXPECTED RESULT:  The summary states that all jobs were successful.
        there is a summary of the errors.
        """
        harvester = CoreHarvester(retry=1)

        jobs = self._create_jobs(n=100)

        # Pick one job and make it fail.  Then add the job as a success at
        # the end.
        jobs[55].result = asyncio.TimeoutError('might happen')

        job = copy.copy(jobs[55])
        job.result = None
        job.num_failures = 1
        jobs.append(job)

        harvester.job_records = jobs

        with self.assertLogs(logger=harvester.logger, level='INFO') as cm:
            harvester.summarize_job_records()

            messages = [
                "Successfully processed 100 records.",
            ]
            self.assertInfoLogMessage(cm.output, messages)

            # The output here is a bit hard to construct, so just get the
            # pieces right.
            message = """
            Error summary:

                               count
            error
            TimeoutError    1
            """
            messages = message.split()
            self.assertErrorLogMessage(cm.output, messages)

    def test_summary_when_one_job_is_skipped(self):
        """
        SCENARIO:  One job is "skipped".  This could happen if one document
        has not been updated.  If it is skipped, it is not retried.

        EXPECTED RESULT:  The summary states that all but one job succeeded.
        """
        harvester = CoreHarvester(retry=1)

        n = 100
        jobs = self._create_jobs(n=n)

        # Pick one job and mark it as being skipped.
        jobs[55].result = SkipError
        harvester.job_records = jobs

        with self.assertLogs(logger=harvester.logger, level='INFO') as cm:
            harvester.summarize_job_records()

            messages = [
                f"Successfully processed {n-1} records.",
            ]
            self.assertInfoLogMessage(cm.output, messages)

            # The output here is a bit hard to construct, so just get the
            # pieces right.
            message = """
            Error summary:

                               count
            error
            SkipError              1
            """
            messages = message.split()
            self.assertErrorLogMessage(cm.output, messages)

    def test_custom_logging(self):
        """
        SCENARIO:  The sitemap has 3 documents.  Invoke with a custom JSON
        logger that logs to a string.  We should see three documents.

        EXPECTED RESULT:  the get_log_messages method returns a string that
        can be loaded by the json module.
        """
        logger = logging.getLogger('test')
        logger.setLevel(logging.INFO)

        logstrings = io.StringIO()
        stream = logging.StreamHandler(logstrings)

        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = jsonlogger.JsonFormatter(format)

        stream.setFormatter(formatter)
        logger.addHandler(stream)

        harvester = CoreHarvester(logger=logger)

        content = ir.read_binary('tests.data.ieda', 'sitemap3.xml')
        doc = lxml.etree.parse(io.BytesIO(content))
        last_harvest = dateutil.parser.parse('1900-01-01T00:00:00Z')

        records = harvester.extract_records_from_sitemap(doc)
        records = harvester.post_process_sitemap_records(records, last_harvest)

        # Retrieve the log messages from the string.
        s = logstrings.getvalue()
        log_entries = s.splitlines()
        s = f"[{','.join(log_entries)}]"
        records = json.loads(s)

        self.assertEqual(len(records), 3)

    def test_lowercase_charset_utf8_xml_header(self):
        """
        SCENARIO:  The Content-Type header for a sitemap is
        'text/xml;charset=utf-8'.

        EXPECTED RESULT:  No warnings are logged.
        """
        headers = {'Content-Type': 'text/xml;charset=utf-8'}
        harvester = CoreHarvester()
        with self.assertLogs(logger=harvester.logger, level='DEBUG') as cm:
            harvester.check_xml_headers(headers)

        self.assertWarningLogCallCount(cm.output, n=0)
