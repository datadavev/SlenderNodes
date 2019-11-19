# Standard library imports
import asyncio
import datetime as dt
try:
    import importlib.resources as ir
except ImportError:  # pragma:  nocover
    import importlib_resources as ir
import io
import re
from unittest.mock import patch

# 3rd party library imports
import aiohttp
from aioresponses import aioresponses
import lxml.etree

# local imports
from schema_org.core import SkipError, XMLValidationError
from schema_org.nkn import NKNHarvester, MissingMetadataFileIdentifierError
from .test_common import TestCommon


class TestSuite(TestCommon):

    def setUp(self):
        # aioresponses can use a regex as a way of catching any URL request
        # with this base.
        self.regex = re.compile("https://www.northwestknowledge.net/data/")

        # The NKN harvesters will use these values.
        self.host, self.port = 'nkn.mn.org', 443

    @patch('schema_org.core.logging.getLogger')
    def test_identifier(self, mock_logger):
        """
        SCENARIO:  The NKN identifier is a UUID that must be retrieved from
        the metadata XML document.

        EXPECTED RESULT:  0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0
        """
        package = 'tests.data.nkn.0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0'
        content = ir.read_binary(package, 'metadata.xml')
        doc = lxml.etree.parse(io.BytesIO(content))

        harvester = NKNHarvester()
        identifier = harvester.extract_series_identifier(doc)

        self.assertEqual(identifier,
                         '0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0')

    def test_sitemap_header__text_html_charset_utf8(self):
        """
        SCENARIO:  The sitemap retrieve header includes 'Content-Type' as
        'text/html;charset=UTF-8'.

        EXPECTED RESULT: No warning is logged.
        """
        content = ir.read_binary('tests.data.nkn', 'index.html')
        headers = {'Content-Type': 'text/html;charset=UTF-8'}

        harvester = NKNHarvester()

        with aioresponses() as m:
            m.get(self.regex, body=content, status=200, headers=headers)

            with self.assertLogs(logger=harvester.logger, level='DEBUG') as cm:
                url = "https://www.northwestknowledge.net/data/"
                asyncio.run(harvester.get_sitemap_document(url))

                self.assertLogLevelCallCount(cm.output, level='WARNING', n=0)

    def test_retrieve_record(self):
        """
        SCENARIO:  We have a URL for a landing page.

        EXPECTED RESULT:  The identifier is retrieved.
        """
        url = (
            "https://www.northwestknowledge.net"
            "/data/0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0/"
        )

        # External I/O
        #
        # 1st:  landing page
        # 2nd:  XML metadata document
        package = 'tests.data.nkn.0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0'
        contents = [
            ir.read_binary(package, 'index.html'),
            ir.read_binary(package, 'metadata.xml')
        ]

        harvester = NKNHarvester()

        with self.assertLogs(logger=harvester.logger, level='INFO'):
            with aioresponses() as m:
                m.get(self.regex, body=contents[0])
                m.get(self.regex, body=contents[1])

                sid, _, doc = asyncio.run(harvester.retrieve_record(url))

        expected = '0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0'
        self.assertEqual(sid, expected)

    def test_retrieve_record__500_error(self):
        """
        SCENARIO:  We have a URL for a landing page.  The response is a server
        error, however.  This is complimentary to the _404_error test below.

        EXPECTED RESULT:  An Exception is raised (but not a SkipError).
        """
        url = (
            "https://www.northwestknowledge.net"
            "/data/94E2D569-200F-44F7-8937-AB4BD0862C91"
        )

        # External I/O
        #
        # 1st:  landing page
        # 2nd:  XML metadata document  (raises 404)
        package = 'tests.data.nkn.0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0'
        contents = [
            ir.read_binary(package, 'index.html'),
        ]

        harvester = NKNHarvester()

        with self.assertLogs(logger=harvester.logger, level='INFO'):
            with aioresponses() as m:
                m.get(self.regex, body=contents[0])
                m.get(self.regex, status=500)

                with self.assertRaises(aiohttp.ClientResponseError):
                    asyncio.run(harvester.retrieve_record(url))

    def test_retrieve_record__404_error(self):
        """
        SCENARIO:  We have a URL for a landing page.  However, the directory
        on the remote end does not have a metadata.xml document.

        EXPECTED RESULT:  A SkipError is raised.  For other clients, this is
        NOT a SkipError.
        """
        url = (
            "https://www.northwestknowledge.net"
            "/data/94E2D569-200F-44F7-8937-AB4BD0862C91"
        )

        # External I/O
        #
        # 1st:  landing page
        # 2nd:  XML metadata document  (raises 404)
        package = 'tests.data.nkn.0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0'
        contents = [
            ir.read_binary(package, 'index.html'),
        ]

        harvester = NKNHarvester()

        with self.assertLogs(logger=harvester.logger, level='INFO'):
            with aioresponses() as m:
                m.get(self.regex, body=contents[0])
                m.get(self.regex, status=404)

                with self.assertRaises(SkipError):
                    asyncio.run(harvester.retrieve_record(url))

    @patch('schema_org.core.logging.getLogger')
    def test_unsupported_xml_format(self, mock_logger):
        """
        SCENARIO:  Sometimes the XML format is not supported.  We have tests
        for this in other places, but NKN is a special case because we have to
        extract the identifier from the XML metadata rather than the JSON-LD.

        This particular file is some sort of ESRI XML file.

        EXPECTED RESULT:  XMLValidationError
        """
        url = (
            "https://www.northwestknowledge.net"
            "/data/A62BEE88-8F92-4649-BC8D-BC56CE96AE2B"
        )

        package = 'tests.data.nkn.A62BEE88-8F92-4649-BC8D-BC56CE96AE2B'
        contents = [
            ir.read_binary(package, 'metadata.xml'),
            ir.read_binary(package, 'index.html'),
        ]

        harvester = NKNHarvester()

        with aioresponses() as m:
            m.get(self.regex, body=contents[0])
            m.get(self.regex, body=contents[1])

            with self.assertRaises(XMLValidationError):
                asyncio.run(harvester.retrieve_record(url))

    def test_missing_file_identifier(self):
        """
        SCENARIO:  The XML metadata file has an empty file identifier field.

        EXPECTED RESULT:  MissingMetadataFileIdentifierError is raised.
        """
        package = 'tests.data.nkn.60795440-42b0-4fb2-a2d4-7e7c00c66aa1'
        content = ir.read_binary(package, 'metadata.xml')
        doc = lxml.etree.parse(io.BytesIO(content))

        harvester = NKNHarvester()

        with self.assertRaises(MissingMetadataFileIdentifierError):
            harvester.extract_series_identifier(doc)

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
        SCENARIO:  One document is to be updated.
        be updated.

        EXPECTED RESULT:  The document is updated, not loaded for the first
        time.  Verify that the sid is a UUID and that the pid is the MD5SUM of
        the metadata document.
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

        harvester = NKNHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap (raw HTML directory listing)
        #   2) Remote HTML document for record 1 (another directory listing)
        #   3) Remote XML document for record 1
        #   4) Existing XML document for record 1 (retrieved from the member
        #      node)
        #
        uuid = '0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0'
        contents = [
            ir.read_binary('tests.data.nkn', 'index.html'),
            ir.read_binary(f'tests.data.nkn.{uuid}', 'index.html'),
            ir.read_binary(f'tests.data.nkn.{uuid}', 'metadata.xml'),
            ir.read_binary(f'tests.data.nkn.{uuid}', 'metadata.prior.xml')
        ]

        status_codes = [200, 200, 200, 200]
        headers = [
            {'Content-Type': 'text/html;charset=UTF-8'},
            {'Content-Type': 'text/html;charset=UTF-8'},
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/xml'},
        ]
        regex = [
            re.compile('https://www.northwestknowledge.net/data/'),
            re.compile('https://www.northwestknowledge.net/data/'),
            re.compile('https://www.northwestknowledge.net/data/'),
            re.compile('https://nkn.mn.org:443/mn/v2/'),
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

        actual = kwargs['system_metadata'].identifier.value()
        expected = '679742d8c458378928ed21b2868db95b'
        self.assertEqual(actual, expected)

        actual = kwargs['system_metadata'].seriesId.value()
        expected = uuid
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
        SCENARIO:  One document is to be loaded for the first time, not
        updated.

        EXPECTED RESULT:  The call counts must reflect that the load routine
        is called and not the update routine. Verify that the sid is a UUID and
        that the pid is the MD5SUM of the metadata document.
        """

        mock_harvest_time.return_value = '1900-01-01T00:00:00Z'
        mock_check_if_identifier_exists.return_value = {'outcome': 'no'}
        mock_update_science_metadata.return_value = True
        mock_load_science_metadata.return_value = True

        harvester = NKNHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap (raw HTML directory listing)
        #   2) Remote HTML document for record 1 (another directory listing)
        #   3) Remote XML document for record 1
        #
        uuid = '0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0'
        contents = [
            ir.read_binary('tests.data.nkn', 'index.html'),
            ir.read_binary(f'tests.data.nkn.{uuid}', 'index.html'),
            ir.read_binary(f'tests.data.nkn.{uuid}', 'metadata.xml'),
        ]

        status_codes = [200, 200, 200]
        headers = [
            {'Content-Type': 'text/html;charset=UTF-8'},
            {'Content-Type': 'text/html;charset=UTF-8'},
            {'Content-Type': 'application/xml'},
        ]
        regex = [
            re.compile('https://www.northwestknowledge.net/data/'),
            re.compile('https://www.northwestknowledge.net/data/'),
            re.compile('https://www.northwestknowledge.net/data/'),
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

        actual = kwargs['system_metadata'].identifier.value()
        expected = '679742d8c458378928ed21b2868db95b'
        self.assertEqual(actual, expected)

        actual = kwargs['system_metadata'].seriesId.value()
        expected = uuid
        self.assertEqual(actual, expected)
