# standard library imports
import asyncio
import datetime as dt
import importlib.resources as ir
import re
from unittest.mock import patch

# 3rd party library imports
from aioresponses import aioresponses

# local imports
from schema_org.arm import ARMHarvester
from .test_common import TestCommon


class TestSuite(TestCommon):

    def setUp(self):
        # aioresponses can use a regex as a way of catching any URL request
        # with this base.
        self.pattern = 'https://www.archive.arm.gov/metadata'
        self.regex = re.compile(self.pattern)

        # The IEDA harvesters will use these values.
        self.host, self.port = 'arm.mn.org', 443

    @patch('schema_org.d1_client_manager.D1ClientManager.load_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.update_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.get_last_harvest_time')  # noqa: E501
    def test_update_run(self,
                        mock_harvest_time,
                        mock_check_if_identifier_exists,
                        mock_update_science_metadata,
                        mock_load_science_metadata):
        """
        SCENARIO:  We have a valid sitemap for one valid document, which is to
        be updated.

        EXPECTED RESULT:  The document is updated, not loaded for the first
        time.  The update occurs with the PID set to the checksum of the xml
        document and the SID set to the DOI.
        """

        record_date = dt.datetime.now()
        mock_harvest_time.return_value = '1900-01-01T00:00:00Z'
        mock_check_if_identifier_exists.return_value = {
            'outcome': 'yes',
            'record_date': record_date - dt.timedelta(days=1),
            'current_version_id': 1,
        }
        mock_update_science_metadata.return_value = True
        mock_load_science_metadata.return_value = True

        harvester = ARMHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap
        #   2) Remote HTML document for record 1
        #   3) Remote XML document for record 1
        #   4) Existing XML document for record 1 (retrieved from the member
        #      node)
        #
        contents = [
            ir.read_binary('tests.data.arm', 'sitemap-1.xml'),
            ir.read_binary('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_binary('tests.data.arm', 'nsasondewnpnS01.b1.fixed.xml'),
            ir.read_binary('tests.data.arm', 'nsasondewnpnS01.b1.prior.xml'),
        ]
        status_codes = [200, 200, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/xml'},
        ]
        regex = [
            re.compile('https://www.archive.arm.gov/metadata/adc'),
            re.compile('https://www.archive.arm.gov/metadata/adc'),
            re.compile('https://www.archive.arm.gov/metadata/adc'),
            re.compile('https://arm.mn.org:443/mn/v2/'),
        ]

        with aioresponses() as m:
            z = zip(regex, contents, status_codes, headers)
            for regex, content, status_code, headers in z:
                m.get(regex, body=content, status=status_code, headers=headers)

            with self.assertLogs(logger=harvester.logger, level='DEBUG'):
                asyncio.run(harvester.run())

        self.assertEqual(mock_load_science_metadata.call_count, 0),
        self.assertEqual(mock_update_science_metadata.call_count, 1),

        # Verify the PID and SID
        args, kwargs = mock_update_science_metadata.call_args_list[0]

        # Verify the PID
        actual = kwargs['system_metadata'].identifier.value()
        expected = 'b96feb9f87705bb03d466ad44289cb11'
        self.assertEqual(actual, expected)

        # Verify the SID
        actual = kwargs['system_metadata'].seriesId.value()
        expected = 'doi:10.5439/1021460'
        self.assertEqual(actual, expected)

    @patch('schema_org.d1_client_manager.D1ClientManager.load_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.update_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.get_last_harvest_time')  # noqa: E501
    def test_load_run(self,
                      mock_harvest_time,
                      mock_check_if_identifier_exists,
                      mock_update_science_metadata,
                      mock_load_science_metadata):
        """
        SCENARIO:  We encounter a document that has not yet been harvested.

        EXPECTED RESULT:  The document is loaded for the first time, not
        updated.  The update occurs with the PID set to the checksum of the
        XML document and the SID set to the DOI.
        """

        mock_harvest_time.return_value = '1900-01-01T00:00:00Z'
        mock_check_if_identifier_exists.return_value = {'outcome': 'no'}
        mock_update_science_metadata.return_value = True
        mock_load_science_metadata.return_value = True

        harvester = ARMHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap
        #   2) Remote HTML document for record 1
        #   3) Remote XML document for record 1
        #   4) Existing XML document for record 1 (retrieved from the member
        #      node)
        #
        contents = [
            ir.read_binary('tests.data.arm', 'sitemap-1.xml'),
            ir.read_binary('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_binary('tests.data.arm', 'nsasondewnpnS01.b1.fixed.xml'),
        ]
        status_codes = [200, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
        ]
        regex = [
            re.compile('https://www.archive.arm.gov/metadata/adc'),
            re.compile('https://www.archive.arm.gov/metadata/adc'),
            re.compile('https://www.archive.arm.gov/metadata/adc'),
        ]

        with aioresponses() as m:
            z = zip(regex, contents, status_codes, headers)
            for regex, content, status_code, headers in z:
                m.get(regex, body=content, status=status_code, headers=headers)

            with self.assertLogs(logger=harvester.logger, level='DEBUG'):
                asyncio.run(harvester.run())

        self.assertEqual(mock_load_science_metadata.call_count, 1),
        self.assertEqual(mock_update_science_metadata.call_count, 0),

        # Verify the PID and SID
        args, kwargs = mock_load_science_metadata.call_args_list[0]

        # Verify the PID
        actual = kwargs['system_metadata'].identifier.value()
        expected = 'b96feb9f87705bb03d466ad44289cb11'
        self.assertEqual(actual, expected)

        # Verify the SID
        actual = kwargs['system_metadata'].seriesId.value()
        expected = 'doi:10.5439/1021460'
        self.assertEqual(actual, expected)

    @patch('schema_org.d1_client_manager.D1ClientManager.get_last_harvest_time')  # noqa: E501
    def test_metadata_document_retrieval_failure(self, mock_harvest_time):
        """
        SCENARIO:  The XML metadata document retrieval fails.

        EXPECTED RESULT:  The failure count goes up by one.
        """

        mock_harvest_time.return_value = '1900-01-01T00:00:00Z'

        harvester = ARMHarvester(host=self.host, port=self.port)

        failed_count = harvester.failed_count

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) XML document for record 1
        #
        contents = [
            ir.read_binary('tests.data.arm', 'sitemap-1.xml'),
            ir.read_binary('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.html'),  # noqa: E501
            ir.read_binary('tests.data.arm', 'nsanimfraod1michC2.c1.xml'),
        ]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
        ]
        status_codes = [200, 200, 400]

        with aioresponses() as m:
            z = zip(contents, headers, status_codes)
            for content, header, status_code in z:
                m.get(self.regex, body=content, headers=header,
                      status=status_code)

            with self.assertLogs(logger=harvester.logger, level='DEBUG') as cm:
                asyncio.run(harvester.run())

                self.assertErrorLogMessage(cm.output, "Bad Request")

        self.assertEqual(harvester.failed_count, failed_count + 1)
