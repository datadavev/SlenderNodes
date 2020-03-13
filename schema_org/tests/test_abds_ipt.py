"""
Test suite for the Arctic Biodiversity Data Service.
"""

# standard library imports
import asyncio
import datetime as dt
import importlib.resources as ir
import io
import re
from unittest.mock import patch

# 3rd party library imports
from aioresponses import aioresponses
import lxml.etree

# local imports
from schema_org.abds import AbdsIptHarvester
from schema_org.d1_client_manager import DATETIME_FORMAT
from .test_common import TestCommon


class TestSuite(TestCommon):

    def setUp(self):
        # Every URL request for ABDS IPT will match this pattern, so we set
        # aioresponses to intercept all of them.
        self.regex = re.compile(r'http://geo.abds.is/ipt')

        # The ABDS IPT harvesters will use these values.
        self.host, self.port = 'abds.mn.org', 443

    def test_sitemap(self):
        """
        SCENARIO:  ABDS IPT has an RSS feed to use as a sitemap.

        EXPECTED RESULT:  70 documents.
        """
        contents = ir.read_binary('tests.data.abds', 'abds_ipt_rss.xml')
        doc = lxml.etree.parse(io.BytesIO(contents))

        harvester = AbdsIptHarvester()
        with self.assertLogs(logger=harvester.logger, level='INFO'):
            records = harvester.extract_records_from_sitemap(doc)

        expected = 70
        self.assertEqual(len(records), expected)

    def test_sitemap_is_index_file(self):
        """
        SCENARIO:  ABDS IPT has an RSS feed to use as a sitemap.

        EXPECTED RESULT:  False, it is not an index file.
        """
        contents = ir.read_binary('tests.data.abds', 'abds_ipt_rss.xml')
        doc = lxml.etree.parse(io.BytesIO(contents))

        harvester = AbdsIptHarvester()
        self.assertFalse(harvester.is_sitemap_index_file(doc))

    def test_identifier(self):
        """
        SCENARIO:  We retrieve an EML 2.1.1 ABDS IPT XML document.

        EXPECTED RESULT:  The identifier is verified.
        """
        content = ir.read_binary('tests.data.abds.ipt', 'arcod_2007p6.xml')

        harvester = AbdsIptHarvester()

        with self.assertLogs(logger=harvester.logger, level='INFO'):
            with aioresponses() as m:
                m.get(self.regex, body=content)

                url = 'http://geo.abds.is/ipt/eml.do?r=arcod_2007p6'
                awaitable = harvester.retrieve_record(url)
                identifier, _, _, _ = asyncio.run(awaitable)

        self.assertEqual(identifier, '59876921-fda6-4fd5-af5d-cba2a7152527')

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
        time.  Verify that the PID has the form UUID/version while the SID is
        just the UUID.
        """

        record_date = dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc)
        mock_harvest_time.return_value = record_date.strftime(DATETIME_FORMAT)
        mock_check_if_identifier_exists.return_value = {
            'outcome': 'yes',
            'record_date': record_date - dt.timedelta(days=1),
            'current_version_id': '59876921-fda6-4fd5-af5d-cba2a7152527/v1.2',
        }
        mock_update_science_metadata.return_value = True
        mock_load_science_metadata.return_value = True

        harvester = AbdsIptHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap (RSS feed)
        #   3) Remote XML document for record 1
        #   4) Existing XML document for record 1 (retrieved from the member
        #      node)
        #
        contents = [
            ir.read_binary('tests.data.abds.ipt', 'rss1.xml'),
            ir.read_binary('tests.data.abds.ipt', 'arcod_2007p6.xml'),
            ir.read_binary('tests.data.abds.ipt', 'arcod_2007p6.previous.xml'),
        ]
        status_codes = [200, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/xml'},
        ]
        regex = [
            re.compile('http://geo.abds.is/ipt'),
            re.compile('http://geo.abds.is/ipt'),
            re.compile('https://abds.mn.org:443/mn/v2/'),
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

        uuid = '59876921-fda6-4fd5-af5d-cba2a7152527'
        version = 'v1.3'

        # Verify the PID
        actual = kwargs['system_metadata'].identifier.value()
        expected = f"{uuid}/{version}"
        self.assertEqual(actual, expected)

        # Verify the SID
        actual = kwargs['system_metadata'].seriesId.value()
        expected = uuid
        self.assertEqual(actual, expected)

    @patch('schema_org.d1_client_manager.D1ClientManager.load_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.update_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.get_last_harvest_time')  # noqa: E501
    def test_new_run(self,
                     mock_harvest_time,
                     mock_check_if_identifier_exists,
                     mock_update_science_metadata,
                     mock_load_science_metadata):
        """
        SCENARIO:  We have a valid sitemap for one valid document, which is a
        document that has not been seen before.

        EXPECTED RESULT:  The document is loaded, not updated.  Verify that the
        PID has the form UUID/version while the SID is just the UUID.
        """

        mock_harvest_time.return_value = '1900-01-01T00:00:00Z'
        mock_check_if_identifier_exists.return_value = {'outcome': 'no'}
        mock_load_science_metadata.return_value = True
        mock_update_science_metadata.return_value = True

        harvester = AbdsIptHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap
        #   2) Remote HTML document for record 1
        #   3) Remote XML document for record 1
        #
        contents = [
            ir.read_binary('tests.data.abds.ipt', 'rss1.xml'),
            ir.read_binary('tests.data.abds.ipt', 'arcod_2007p6.xml'),
            ir.read_binary('tests.data.abds.ipt', 'arcod_2007p6.previous.xml'),
        ]
        status_codes = [200, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/html'},
            {'Content-Type': 'application/xml'},
        ]
        regex = [
            re.compile('http://geo.abds.is/ipt'),
            re.compile('http://geo.abds.is/ipt'),
            re.compile('https://abds.mn.org:443/mn/v2/'),
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

        uuid = '59876921-fda6-4fd5-af5d-cba2a7152527'
        version = 'v1.3'

        # Verify the PID
        actual = kwargs['system_metadata'].identifier.value()
        expected = f"{uuid}/{version}"
        self.assertEqual(actual, expected)

        # Verify the SID
        actual = kwargs['system_metadata'].seriesId.value()
        expected = uuid
        self.assertEqual(actual, expected)

    def test_generate_system_metadata(self):
        """
        SCENARIO:  IEDA system metadata generation.

        EXPECTED RESULT:  The series ID is the native identifier sid and the
        identifier (pid) is the record version.
        """

        harvester = AbdsIptHarvester(host=self.host, port=self.port)

        native_identifier_sid = '59876921-fda6-4fd5-af5d-cba2a7152527'
        record_version = '59876921-fda6-4fd5-af5d-cba2a7152527/v1.3'
        kwargs = {
            'scimeta_bytes':  ir.read_binary('tests.data.abds.ipt', 'arcod_2007p6.xml'),  # noqa : E501
            'native_identifier_sid':  native_identifier_sid,
            'record_date':  dt.datetime.now(),
            'record_version': record_version,
        }
        sysmeta = harvester.generate_system_metadata(**kwargs)

        self.assertEqual(sysmeta.seriesId.value(), native_identifier_sid)
        self.assertEqual(sysmeta.identifier.value(), record_version)
