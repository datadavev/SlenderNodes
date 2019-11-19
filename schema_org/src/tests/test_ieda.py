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
from schema_org.core import SITEMAP_NS
from schema_org.jsonld_validator import JsonLdError
from schema_org.ieda import IEDAHarvester
from .test_common import TestCommon


class TestSuite(TestCommon):

    def setUp(self):
        # aioresponses can use a regex as a way of catching any URL request
        # with this base.
        self.pattern = 'http://get.iedadata.org/'
        self.regex = re.compile(self.pattern)

        # The IEDA harvesters will use these values.
        self.host, self.port = 'ieda.mn.org', 443

    def test_series_identifier__doi_style__extra_space(self):
        """
        SCENARIO:  We have JSON-LD from an IEDA landing page.  There is a
        leading space in the JSON-LD field that must be stripped.

        EXPECTED RESULT:  The series ID is verified.
        """

        contents = ir.read_binary('tests.data.ieda', 'ieda600048.html')
        doc = lxml.etree.HTML(contents)

        harvester = IEDAHarvester()
        j = harvester.extract_jsonld(doc)

        sid = harvester.extract_series_identifier(j)

        self.assertEqual(sid, '10.15784/600048')

    def test_record_version__600048(self):
        """
        SCENARIO:  Extract the record version (pid) for an IEDA document.

        EXPECTED RESULT:  The record version is verified.  For IEDA,
        the landing page URL is the record version (PID).
        """

        harvester = IEDAHarvester()

        landing_page_url = 'http://get.iedadata.org/metadata/iso/600048'
        pid = harvester.extract_record_version(None, landing_page_url)

        self.assertEqual(pid, landing_page_url)

    def test_extract_series_identifier__other_style(self):
        """
        SCENARIO:  We have JSON-LD from an IEDA landing page.

        EXPECTED RESULT:  The identifier is verified.
        """

        contents = ir.read_binary('tests.data.ieda', 'ieda609246.html')
        doc = lxml.etree.HTML(contents)

        harvester = IEDAHarvester()

        j = harvester.extract_jsonld(doc)
        sid = harvester.extract_series_identifier(j)

        self.assertEqual(sid, 'urn:usap-dc:metadata:609246')
        # self.assertEqual(pid, 'http://get.iedadata.org/metadata/iso/609246')

    def test_extract_series_identifier__unparseable_id(self):
        """
        SCENARIO:  We have JSON-LD from an IEDA landing page.  The '@id' field
        isn't of the right form.

        EXPECTED RESULT:  A JsonLDError is raised.
        """
        j = {'@id':  'ftp://oid:10.15784/600048'}

        harvester = IEDAHarvester()

        with self.assertRaises(JsonLdError):
            harvester.extract_series_identifier(j)

    def test_extract_url__too_many_metadata_urls(self):
        """
        SCENARIO:  We have JSON-LD from an IEDA landing page.  The
        'distribution' key has more than one list item for an 'ISO Metadata
        Document' field.  We don't necessarily know which one to use.  This is
        admittedly an extreme edge case.

        EXPECTED RESULT:  A JsonLDError is raised.
        """
        j = {
            '@id':  'https://dx.doi.org:10.15784/600048',
            'distribution': [
                {
                    'url': 'https://get.ieda.org/doc1.xml',
                    'name': 'ISO Metadata Document',
                },
                {
                    'url': 'https://get.ieda.org/doc2.xml',
                    'name': 'ISO Metadata Document',
                },
            ]
        }

        harvester = IEDAHarvester()

        with self.assertRaises(JsonLdError):
            harvester.extract_metadata_url(j)

    @patch('schema_org.d1_client_manager.D1ClientManager.update_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    def test_document_already_harvested_but_can_be_successfully_updated(
        self,
        mock_check_if_identifier_exists,
        mock_update_science_metadata
    ):
        """
        SCENARIO:  The GMN existance check shows that the document has already
        been harvested.  It has been updated since the last harvest time, and
        the update succeeds.

        The document in question has a DOI of doi:10.15784/600121

        EXPECTED RESULT:  The event is logged at the info level.  The update
        count increases by one.  The update_science_metadata routine should
        have been called with specific parameters.
        """
        harvester = IEDAHarvester(host=self.host, port=self.port)

        # This is the existing document in the MN.  It is marked as complete.
        existing_content = ir.read_binary('tests.data.ieda', '600121iso.xml')

        record_date = dt.datetime.now()
        mock_check_if_identifier_exists.return_value = {
            'outcome': 'yes',
            'record_date': record_date - dt.timedelta(days=1),
            'current_version_id': 1,
        }
        mock_update_science_metadata.return_value = True

        harvester = IEDAHarvester(host=self.host, port=self.port)
        update_count = harvester.updated_count

        # This is the "update" document, same as the existing document.  It is
        # already marked as "complete".  Bump the timestamp to just a bit later
        # to make ok to proceed.
        docbytes = ir.read_binary('tests.data.ieda', '600121iso-later.xml')
        doc = lxml.etree.parse(io.BytesIO(docbytes))
        doi = 'doi:10.15784/600121'
        pid = 'https://get.iedadata.org/metadata/iso/600121'

        regex = re.compile('https://ieda.mn.org:443/')
        with self.assertLogs(logger=harvester.logger, level='DEBUG') as cm:
            with aioresponses() as m:
                m.get(regex, body=existing_content)
                asyncio.run(harvester.harvest_document(doi, pid, doc,
                                                       record_date))

            # Did we see a warning?
            self.assertLogLevelCallCount(cm.output, level='INFO', n=1)

            # Did we increase the update count?
            self.assertEqual(harvester.updated_count, update_count + 1)

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
        time.
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

        harvester = IEDAHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap
        #   2) Remote HTML document for record 1
        #   3) Remote XML document for record 1
        #   4) Existing XML document for record 1 (retrieved from the member
        #      node)
        #
        contents = [
            ir.read_binary('tests.data.ieda', 'sitemap-1.xml'),
            ir.read_binary('tests.data.ieda', 'ieda609246.html'),
            ir.read_binary('tests.data.ieda', '609246.xml'),
            ir.read_binary('tests.data.ieda', '609246-existing.xml')
        ]
        status_codes = [200, 200, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/html'},
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/xml'},
        ]
        regex = [
            re.compile('http://get.iedadata.org/'),
            re.compile('http://get.iedadata.org/'),
            re.compile('http://get.iedadata.org/'),
            re.compile('https://ieda.mn.org:443/mn/v2/'),
        ]

        with aioresponses() as m:
            z = zip(regex, contents, status_codes, headers)
            for regex, content, status_code, headers in z:
                m.get(regex, body=content, status=status_code, headers=headers)

            with self.assertLogs(logger=harvester.logger, level='DEBUG'):
                asyncio.run(harvester.run())

        self.assertEqual(mock_load_science_metadata.call_count, 0),
        self.assertEqual(mock_update_science_metadata.call_count, 1),

    def _docbytes(self, landing_page_url):
        """
        Construct a byte stream of a sitemap document.
        """
        urlset = lxml.etree.Element(f"{{{SITEMAP_NS['sm']}}}urlset")
        url = lxml.etree.SubElement(urlset, f"{{{SITEMAP_NS['sm']}}}url")

        loc = lxml.etree.SubElement(url, f"{{{SITEMAP_NS['sm']}}}loc")
        loc.text = landing_page_url

        lastmod = lxml.etree.SubElement(url, f"{{{SITEMAP_NS['sm']}}}lastmod")
        lastmod.text = "2018-06-21T22:05:27-04:00"

        docbytes = lxml.etree.tostring(urlset)
        return docbytes

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
        SCENARIO:  We have a valid sitemap for one valid document, which is a
        document that has not been seen before.

        EXPECTED RESULT:  The document is loaded, not updated.  Verify that the
        PID is the URL of a landing page and the SID is a DOI.
        """
        record_date = dt.datetime.now()
        mock_harvest_time.return_value = '1900-01-01T00:00:00Z'
        mock_check_if_identifier_exists.return_value = {
            'outcome': 'yes',
            'record_date': record_date - dt.timedelta(days=1),
            'current_version_id': 1,
        }
        mock_load_science_metadata.return_value = True
        mock_update_science_metadata.return_value = True

        landing_page_url = "http://get.iedadata.org/metadata/iso/609246"
        docbytes = self._docbytes(landing_page_url)

        harvester = IEDAHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap
        #   2) Remote HTML document for record 1
        #   3) Remote XML document for record 1
        #   4) Prior existing record in MN for record 1
        #
        contents = [
            docbytes,
            ir.read_binary('tests.data.ieda', 'ieda609246.html'),
            ir.read_binary('tests.data.ieda', '609246.xml'),
            ir.read_binary('tests.data.ieda', '609246-existing.xml'),
        ]
        status_codes = [200, 200, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/html'},
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/xml'},
        ]
        regex = [
            re.compile('http://get.iedadata.org/'),
            re.compile('http://get.iedadata.org/'),
            re.compile('http://get.iedadata.org/'),
            re.compile('https://ieda.mn.org:443/mn/v2'),
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
        expected = landing_page_url
        self.assertEqual(actual, expected)

        # Verify the SID
        actual = kwargs['system_metadata'].seriesId.value()
        expected = 'urn:usap-dc:metadata:609246'
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
        PID is the URL of a landing page and the SID is a DOI.
        """

        mock_harvest_time.return_value = '1900-01-01T00:00:00Z'
        mock_check_if_identifier_exists.return_value = {'outcome': 'no'}
        mock_load_science_metadata.return_value = True
        mock_update_science_metadata.return_value = True

        landing_page_url = "http://get.iedadata.org/metadata/iso/609246"
        docbytes = self._docbytes(landing_page_url)

        harvester = IEDAHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap
        #   2) Remote HTML document for record 1
        #   3) Remote XML document for record 1
        #
        contents = [
            docbytes,
            ir.read_binary('tests.data.ieda', 'ieda609246.html'),
            ir.read_binary('tests.data.ieda', '609246.xml'),
        ]
        status_codes = [200, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/html'},
            {'Content-Type': 'application/xml'},
        ]
        regex = [
            re.compile('http://get.iedadata.org/'),
            re.compile('http://get.iedadata.org/'),
            re.compile('http://get.iedadata.org/'),
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
        expected = landing_page_url
        self.assertEqual(actual, expected)

        # Verify the SID
        actual = kwargs['system_metadata'].seriesId.value()
        expected = 'urn:usap-dc:metadata:609246'
        self.assertEqual(actual, expected)

    def test_generate_system_metadata(self):
        """
        SCENARIO:  IEDA system metadata generation.

        EXPECTED RESULT:  The series ID is the native identifier sid and the
        identifier (pid) is the record version.
        """

        harvester = IEDAHarvester(host=self.host, port=self.port)

        native_identifier_sid = 'urn:usap-dc:metadata:609246'
        record_version = 'http://get.iedadata.org/metadata/iso/609246'
        kwargs = {
            'scimeta_bytes':  ir.read_binary('tests.data.ieda', '609246.xml'),
            'native_identifier_sid':  native_identifier_sid,
            'record_date':  dt.datetime.now(),
            'record_version': record_version,
        }
        sysmeta = harvester.generate_system_metadata(**kwargs)

        self.assertEqual(sysmeta.seriesId.value(), native_identifier_sid)
        self.assertEqual(sysmeta.identifier.value(), record_version)
