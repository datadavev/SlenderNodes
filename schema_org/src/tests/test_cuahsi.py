# standard library imports
import asyncio
import datetime as dt
import hashlib
import importlib.resources as ir
import io
import json
import re
from unittest.mock import patch
import zipfile

# 3rd party library imports
from aioresponses import aioresponses
import lxml.etree

# local imports
from schema_org.core import SkipError, XMLMetadataParsingError
from schema_org.cuahsi import CUAHSIHarvester
from schema_org.jsonld_validator import JsonLdError
from .test_common import TestCommon


class TestSuite(TestCommon):

    def setUp(self):
        # Every URL request for CUAHSI will match this pattern, so we set
        # aioresponses to intercept all of them.
        self.regex = re.compile(r'https://www.hydroshare.org/')

        # The IEDA harvesters will use these values.
        self.host, self.port = 'cuahsi.mn.org', 443

    def test_landing_page_is_published(self):
        """
        SCENARIO:  A landing page indicates that it is published.
        Such an element is needed because we only wish to harvest PUBLISHED
        documents.

        EXPECTED RESULT:  No exception is raised.
        """

        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75'
        contents = ir.read_text(package, 'landing_page.html')
        doc = lxml.etree.HTML(contents)

        obj = CUAHSIHarvester()

        with self.assertLogs(logger=obj.logger, level='DEBUG'):
            obj.preprocess_landing_page(doc)

    def test_landing_page_is_not_published(self):
        """
        SCENARIO:  A landing page indicates that it is not published.

        EXPECTED RESULT:  A SkipError is raised.
        """

        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75'
        contents = ir.read_text(package, 'landing_page.not_published.html')
        doc = lxml.etree.HTML(contents)

        obj = CUAHSIHarvester()

        with self.assertLogs(logger=obj.logger, level='DEBUG'):
            with self.assertRaises(SkipError):
                obj.preprocess_landing_page(doc)

    def test_landing_page_does_not_have_sharing_status_element(self):
        """
        SCENARIO:  A landing page does not have a sharing status element.
        Such an element is needed because we only wish to harvest PUBLISHED
        documents.

        EXPECTED RESULT:  A SkipError is raised.
        """

        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75'
        contents = ir.read_text(package, 'landing_page.no_sharing_status.html')
        doc = lxml.etree.HTML(contents)

        obj = CUAHSIHarvester()

        with self.assertLogs(logger=obj.logger, level='DEBUG'):
            with self.assertRaises(SkipError):
                obj.preprocess_landing_page(doc)

    def test_landing_page_jsonld(self):
        """
        SCENARIO:  A landing page does have a JSON-LD <SCRIPT> element.

        EXPECTED RESULT:  The JSON-LD is loaded.
        """
        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75'
        contents = ir.read_text(package, 'landing_page.html')
        doc = lxml.etree.HTML(contents)

        obj = CUAHSIHarvester()

        with self.assertLogs(logger=obj.logger, level='DEBUG'):
            j = obj.get_jsonld(doc)

        # To make sure we have JSON, feed it to something that expects it.
        json.dumps(j)

    def test_landing_page_is_missing_jsonld(self):
        """
        SCENARIO:  A landing page does not have a JSON-LD <SCRIPT> element.

        EXPECTED RESULT:  A SkipError is raised.  Many CUAHSI documents
        don't have JSON-LD, and we don't want that counting against the
        failure count.
        """
        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75'
        contents = ir.read_text(package, 'landing_page.no_json_ld.html')
        doc = lxml.etree.HTML(contents)

        obj = CUAHSIHarvester()

        with self.assertLogs(logger=obj.logger, level='DEBUG'):
            with self.assertRaises(JsonLdError):
                obj.get_jsonld(doc)

    def test_retrieve_record(self):
        """
        SCENARIO:  We have a URL for a landing page for a PUBLISHED document.

        EXPECTED RESULT:  The identifier is retrieved.
        """
        url = (
            'https://www.hydroshare.org'
            '/resource/81e947faccf04de59392dddaac77bc75/'
        )

        # External I/O
        #
        # 1st:  landing page
        # 2nd:  zip archive containing data and metadata
        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75'
        contents1 = ir.read_text(package, 'landing_page.html')

        b = io.BytesIO()
        zf = zipfile.ZipFile(b, mode='w')
        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75.data'
        content = ir.read_binary(package, 'resourcemetadata.xml')
        zf.writestr('81e947faccf04de59392dddaac77bc75/data/resourcemetadata',
                    content)
        zf.close()
        b.seek(0)
        contents2 = b.read()

        harvester = CUAHSIHarvester()

        with self.assertLogs(logger=harvester.logger, level='INFO'):
            with aioresponses() as m:
                m.get(self.regex, body=contents1)
                m.get(self.regex, body=contents2)

                sid, pid, doc = asyncio.run(harvester.retrieve_record(url))

        self.assertEqual(sid, '10.4211/hs.81e947faccf04de59392dddaac77bc75')

    def test_retrieve_record__no_url_for_zip_archive(self):
        """
        SCENARIO:  We have a URL for a landing page for a PUBLISHED document,
        but the landing page does not have a proper URL for the bagit zip
        archive.  Yeah, this happens.

        EXPECTED RESULT:  A SkipError is issued.
        """
        url = (
            'https://www.hydroshare.org'
            '/resource/81e947faccf04de59392dddaac77bc75/'
        )

        # External I/O
        #
        # 1st:  landing page
        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75'
        contents1 = ir.read_text(package, 'landing_page.no_zip_url.html')

        harvester = CUAHSIHarvester()

        with self.assertLogs(logger=harvester.logger, level='INFO'):
            with aioresponses() as m:
                m.get(self.regex, body=contents1)

                with self.assertRaises(SkipError):
                    asyncio.run(harvester.retrieve_record(url))

    def test_retrieve_record__bad_metadata_document(self):
        """
        SCENARIO:  We have a URL for a landing page for a PUBLISHED document.
        The metadata document, however, is invalid.

        EXPECTED RESULT:  An XMLMetadataParsingError is issued.
        """
        url = (
            'https://www.hydroshare.org'
            '/resource/81e947faccf04de59392dddaac77bc75/'
        )

        # External I/O
        #
        # 1st:  landing page
        # 2nd:  zip archive containing data and metadata
        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75'
        contents1 = ir.read_text(package, 'landing_page.html')

        # Switch out the metadata document for something that is NOT xml.
        b = io.BytesIO()
        zf = zipfile.ZipFile(b, mode='w')
        zf.writestr('81e947faccf04de59392dddaac77bc75/data/resourcemetadata',
                    b'not xml')
        zf.close()
        b.seek(0)
        contents2 = b.read()

        harvester = CUAHSIHarvester()

        with self.assertLogs(logger=harvester.logger, level='INFO'):
            with aioresponses() as m:
                m.get(self.regex, body=contents1)
                m.get(self.regex, body=contents2)

                with self.assertRaises(XMLMetadataParsingError):
                    asyncio.run(harvester.retrieve_record(url))

    @patch('schema_org.d1_client_manager.D1ClientManager.get_last_harvest_time')  # noqa: E501
    def test__harvest__but_landing_page_has_no_json_ld(self,
                                                       harvest_time_mocker):
        """
        SCENARIO:  We have a valid sitemap but one of the landing pages does
        not have any JSON-LD.

        EXPECTED RESULT:  A SkipError is issued and caught.
        """

        harvest_time_mocker.return_value = '1900-01-01T00:00:00Z'

        host, port = 'www.hydroshare.org', 443
        harvester = CUAHSIHarvester(host=host, port=port)

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #
        contents = [
            ir.read_binary('tests.data.cuahsi',
                           'sitemap.81e947faccf04de59392dddaac77bc75.xml'),
            ir.read_binary('tests.data.cuahsi.81e947faccf04de59392dddaac77bc75',  # noqa : E501
                           'landing_page.no_json_ld.html')
        ]
        status_codes = [200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/html'},
        ]

        z = zip(contents, status_codes, headers)
        with aioresponses() as m:
            for content, status_code, headers in z:
                m.get(self.regex,
                      body=content, status=status_code, headers=headers)

            with self.assertLogs(logger=harvester.logger, level='DEBUG') as cm:
                asyncio.run(harvester.run())

                expected = "Successfully processed 0 records."
                self.assertInfoLogMessage(cm.output, expected)

                expected = "No JSON-LD <SCRIPT> elements were located"
                self.assertWarningLogMessage(cm.output, expected)

                expected = "SkipError"
                self.assertErrorLogMessage(cm.output, expected)

    @patch('schema_org.d1_client_manager.D1ClientManager.load_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.get_last_harvest_time')  # noqa: E501
    def test__harvest__landing_page_errors__succeeds_on_retry(
        self,
        harvest_time_mocker,
        mock_check_if_identifier_exists,
        mock_load_science_metadata
    ):
        """
        SCENARIO:  We have a valid sitemap but the landing page errors out.
        A retry is specified, and it succeeds the next time.

        EXPECTED RESULT:  The document is successfully harvested.
        """

        harvest_time_mocker.return_value = '1900-01-01T00:00:00Z'
        mock_check_if_identifier_exists.return_value = {'outcome': 'no'}
        mock_load_science_metadata.return_value = True

        host, port = 'www.hydroshare.org', 443
        harvester = CUAHSIHarvester(host=host, port=port, retry=1)

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) HTML document for record 1, 2nd try
        #   4) ZIP archive for record 1
        #
        contents = [
            ir.read_binary('tests.data.cuahsi',
                           'sitemap.81e947faccf04de59392dddaac77bc75.xml'),
            ir.read_binary('tests.data.cuahsi.81e947faccf04de59392dddaac77bc75',  # noqa : E501
                           'landing_page.html'),
            ir.read_binary('tests.data.cuahsi.81e947faccf04de59392dddaac77bc75',  # noqa : E501
                           'landing_page.html')
        ]

        b = io.BytesIO()
        zf = zipfile.ZipFile(b, mode='w')
        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75.data'
        content = ir.read_binary(package, 'resourcemetadata.xml')
        zf.writestr('81e947faccf04de59392dddaac77bc75/data/resourcemetadata',
                    content)
        zf.close()
        b.seek(0)
        contents.append(b.read())

        status_codes = [200, 400, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/html'},
            {'Content-Type': 'application/html'},
            {'Content-Type': 'application/zip'},
        ]

        z = zip(contents, status_codes, headers)
        with aioresponses() as m:
            for content, status_code, headers in z:
                m.get(self.regex,
                      body=content, status=status_code, headers=headers)

            with self.assertLogs(logger=harvester.logger, level='DEBUG') as cm:
                asyncio.run(harvester.run())

                expected = "Successfully processed 1 records."
                self.assertInfoLogMessage(cm.output, expected)

                expected = "Bad Request"
                self.assertErrorLogMessage(cm.output, expected)

                expected = "ClientResponseError"
                self.assertErrorLogMessage(cm.output, expected)

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
        time.  Verify that the sid is a DOI and that the pid is the MD5SUM of
        the zip archive.
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

        harvester = CUAHSIHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap
        #   2) Remote HTML document for record 1
        #   3) Remote XML document for record 1
        #   4) Existing XML document for record 1 (retrieved from the member
        #      node)
        #
        b = io.BytesIO()
        zf = zipfile.ZipFile(b, mode='w')
        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75.data'
        content = ir.read_binary(package, 'resourcemetadata.xml')
        zf.writestr('81e947faccf04de59392dddaac77bc75/data/resourcemetadata',
                    content)
        zf.close()
        b.seek(0)
        zip_archive_content = b.read()

        contents = [
            ir.read_binary('tests.data.cuahsi', 'sitemap1.xml'),
            ir.read_binary('tests.data.cuahsi.81e947faccf04de59392dddaac77bc75', 'landing_page.html'),  # noqa : E501
            zip_archive_content,
            ir.read_binary('tests.data.cuahsi.81e947faccf04de59392dddaac77bc75.data', 'resourcemetadata.previous.xml'),  # noqa : E501
        ]

        status_codes = [200, 200, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/html'},
            {'Content-Type': 'application/zip'},
            {'Content-Type': 'application/xml'},
        ]
        regex = [
            re.compile('https://www.hydroshare.org/'),
            re.compile('https://www.hydroshare.org/'),
            re.compile('https://www.hydroshare.org/'),
            re.compile('https://cuahsi.mn.org:443/mn/v2/'),
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
        expected = hashlib.md5(zip_archive_content).hexdigest()
        self.assertEqual(actual, expected)

        actual = kwargs['system_metadata'].seriesId.value()
        expected = '10.4211/hs.81e947faccf04de59392dddaac77bc75'
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
        sid is a DOI and that the pid is the MD5SUM of the zip archive.
        """

        mock_harvest_time.return_value = '1900-01-01T00:00:00Z'
        mock_check_if_identifier_exists.return_value = {'outcome': 'no'}
        mock_load_science_metadata.return_value = True
        mock_update_science_metadata.return_value = True

        harvester = CUAHSIHarvester(host=self.host, port=self.port)

        # External calls to read the:
        #
        #   1) sitemap
        #   2) Remote HTML document for record 1
        #   3) Remote Zip archive (contains metadata)
        #

        contents = [
            ir.read_binary('tests.data.cuahsi', 'sitemap1.xml'),
            ir.read_binary('tests.data.cuahsi.81e947faccf04de59392dddaac77bc75', 'landing_page.html'),  # noqa : E501
        ]

        b = io.BytesIO()
        zf = zipfile.ZipFile(b, mode='w')
        package = 'tests.data.cuahsi.81e947faccf04de59392dddaac77bc75.data'
        content = ir.read_binary(package, 'resourcemetadata.xml')
        zf.writestr('81e947faccf04de59392dddaac77bc75/data/resourcemetadata',
                    content)
        zf.close()
        b.seek(0)
        zip_archive_content = b.read()

        contents.append(zip_archive_content)

        status_codes = [200, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/html'},
            {'Content-Type': 'application/zip'},
        ]
        regex = [
            re.compile('https://www.hydroshare.org/'),
            re.compile('https://www.hydroshare.org/'),
            re.compile('https://www.hydroshare.org/'),
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
        expected = hashlib.md5(zip_archive_content).hexdigest()
        self.assertEqual(actual, expected)

        # Verify the SID
        actual = kwargs['system_metadata'].seriesId.value()
        expected = '10.4211/hs.81e947faccf04de59392dddaac77bc75'
        self.assertEqual(actual, expected)
