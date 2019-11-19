"""
Test suite for schema.org core functionality.
"""

# Standard library imports
import asyncio
import datetime as dt
try:
    import importlib.resources as ir
except ImportError:  # pragma:  nocover
    import importlib_resources as ir
import io
import json
import re
from unittest.mock import patch

# 3rd party library imports
import aiohttp
from aioresponses import aioresponses
import lxml.etree

# local imports
from schema_org.so_core import SchemaDotOrgHarvester
import schema_org.core
from .test_common import TestCommon


class TestSuite(TestCommon):

    def setUp(self):
        # aioresponses can use a regex as a way of catching any URL request
        # with this base.
        self.pattern = 'https://www.archive.arm.gov/metadata/adc'
        self.regex = re.compile(self.pattern)

    def test_jsonld_script_element_is_missing(self):
        """
        SCENARIO:  In ARM, there are usually two <SCRIPT> elements with
        JSON-LD, but the first one is the one we want.  In this test case,
        it is not present.

        EXPECTED RESULT:  RuntimeError
        """
        text = ir.read_binary('tests.data.arm',
                              'nsaqcrad1longC2.c2.no_json_ld.html')
        doc = lxml.etree.HTML(text)

        harvester = SchemaDotOrgHarvester()
        with self.assertRaises(RuntimeError):
            harvester.get_jsonld(doc)

    def test_jsonld_script_element_has_no_dataset(self):
        """
        SCENARIO:  In ARM, there are usually two <SCRIPT> elements with
        JSON-LD, but the first one is the one we want.  In this test case,
        only the 2nd is present, which has no useful information.

        EXPECTED RESULT:  RuntimeError
        """
        text = ir.read_binary('tests.data.arm',
                              'nsaqcrad1longC2.c2.no_useful_json_ld.html')
        doc = lxml.etree.HTML(text)

        harvester = SchemaDotOrgHarvester()
        with self.assertRaises(RuntimeError):
            harvester.get_jsonld(doc)

    def test_jsonld_script_element_is_first(self):
        """
        SCENARIO:  In ARM, there are usually two <SCRIPT> elements with
        JSON-LD, but the first one is the one we want.  In this test case,
        the first <SCRIPT> element has the JSON-LD.

        EXPECTED RESULT:  The JSON-LD with @type Dataset is parsed.
        """
        text = ir.read_binary('tests.data.arm',
                              'nsaqcrad1longC2.c2.fixed.html')
        doc = lxml.etree.HTML(text)

        harvester = SchemaDotOrgHarvester()
        j = harvester.get_jsonld(doc)
        self.assertEqual(j['@type'], 'Dataset')

    def test_jsonld_script_element_is_second(self):
        """
        SCENARIO:  In ARM, there are usually two <SCRIPT> elements with
        JSON-LD, but the first one is the one we want.  In this test case,
        the second  <SCRIPT> element has the JSON-LD.

        EXPECTED RESULT:  The JSON-LD with @type Dataset is parsed.
        """
        text = ir.read_binary('tests.data.arm',
                              'nsaqcrad1longC2.c2.swapped_scripts.html')
        doc = lxml.etree.HTML(text)

        harvester = SchemaDotOrgHarvester()
        j = harvester.get_jsonld(doc)
        self.assertEqual(j['@type'], 'Dataset')

    @patch('schema_org.core.logging.getLogger')
    def test_identifier_parsing(self, mock_logger):
        """
        SCENARIO:  The @id field from the JSON-LD must be parsed, we are
        presented with http://dx.doi.org/10.5439/1027257.

        EXPECTED RESULT:  The ID "10.5439/1027257" is returned.
        """
        jsonld = {'@id': 'http://dx.doi.org/10.5439/1027257'}
        harvester = SchemaDotOrgHarvester()
        identifier = harvester.extract_series_identifier(jsonld)

        self.assertEqual(identifier, 'doi:10.5439/1027257')

    @patch('schema_org.core.logging.getLogger')
    def test_identifier_parsing_error(self, mock_logger):
        """
        SCENARIO:  The @id field from the JSON-LD must be parsed, but the given
        field is bad.

        EXPECTED RESULT:  A RuntimeError is raised.
        """
        jsonld = {'@id': 'http://dx.doi.orggg/10.5439/1027257'}
        harvester = SchemaDotOrgHarvester()

        with self.assertRaises(RuntimeError):
            harvester.extract_series_identifier(jsonld)

    @patch('schema_org.d1_client_manager.D1ClientManager.load_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.get_last_harvest_time')  # noqa: E501
    def test__last_harvest_time_gt_lastmod(self,
                                           mock_harvest_time,
                                           mock_check_if_identifier_exists,
                                           mock_load_science_metadata):
        """
        SCENARIO:  We have a valid sitemap and valid documents.  One of the
        documents, though, was harvested since it was last modified.

        EXPECTED RESULT:  No errors are logged.  A message is logged that the
        one record was skipped.
        """

        # Set the harvest time ahead of the lastmod time.  If we're still
        # running this code in the 23rd century, well dang...
        mock_harvest_time.return_value = '2200-01-01T00:00:00Z'
        mock_check_if_identifier_exists.return_value = {'outcome': 'no'}
        mock_load_science_metadata.return_value = True

        harvester = SchemaDotOrgHarvester(host='test.arm.gov')
        harvester.sitemap_url = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'  # noqa: E501

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) XML document for record 1
        #
        contents = [
            ir.read_binary('tests.data.arm', 'sitemap-1.xml'),
            ir.read_binary('tests.data.arm',
                           'nsanimfraod1michC2.c1.fixed.html'),
            ir.read_binary('tests.data.arm',
                           'nsanimfraod1michC2.c1.fixed.xml'),
        ]
        status_codes = [200, 200, 200]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'application/html'},
            {'Content-Type': 'application/xml'},
        ]

        z = zip(contents, status_codes, headers)
        with aioresponses() as m:
            for content, status_code, headers in z:
                m.get(self.regex,
                      body=content, status=status_code, headers=headers)

            with self.assertLogs(logger=harvester.logger, level='DEBUG') as cm:
                asyncio.run(harvester.run())

                self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)
                expected = "Successfully processed 0 records."
                self.assertInfoLogMessage(cm.output, expected)

                expected = '1 records skipped'
                self.assertInfoLogMessage(cm.output, expected)

    def test_identifier_parsing_error__space(self):
        """
        SCENARIO:  The @id field from the JSON-LD must be parsed, there is a
        space in the @id entry.

        EXPECTED RESULT:  RuntimeError
        """
        harvester = SchemaDotOrgHarvester()
        jsonld = {'@id': " doi:10.15784/601015"}
        with self.assertRaises(RuntimeError):
            harvester.extract_series_identifier(jsonld)

    def test_metadata_document_retrieval(self):
        """
        SCENARIO:  an IEDA metadata document URL is retrieved and properly
        transformed.

        EXPECTED RESULT:  A byte-stream of a valid metadata document.  There
        are no ERROR or WARNING messages logged.
        """

        url = self.pattern + '/600121iso.xml'
        harvester = SchemaDotOrgHarvester()

        content = ir.read_binary('tests.data.ieda', '600121iso.xml')
        with self.assertLogs(logger=harvester.logger, level='DEBUG') as cm:
            with aioresponses() as m:
                m.get(self.regex, body=content)
                doc1 = asyncio.run(harvester.retrieve_metadata_document(url))

            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)
            self.assertLogLevelCallCount(cm.output, level='WARNING', n=0)

        doc2 = lxml.etree.parse(io.BytesIO(content))
        self.assertEqual(lxml.etree.tostring(doc1), lxml.etree.tostring(doc2))

    @patch('schema_org.core.logging.getLogger')
    def test_metadata_document_retrieval_httperror(self, log_mocker):
        """
        SCENARIO:  an IEDA metadata document URL retrieval results in a
        requests.HTTPError exception being raised.

        EXPECTED RESULT:  An HTTPError is raised.
        """
        harvester = SchemaDotOrgHarvester()

        url = 'http://get.iedadata.org/600121iso.xml'

        with self.assertRaises(aiohttp.client_exceptions.ClientResponseError):
            with aioresponses() as m:
                m.get(url, status=400)
                asyncio.run(harvester.retrieve_metadata_document(url))

    def test_ieda_600165_unescaped_double_quotes(self):
        """
        SCENARIO:  The HTML file has invalid JSONLD embedded in its SCRIPT.
        Two description fields have unescaped double-quotes.

        EXPECTED RESULT:  An exception is issued.
        """
        harvester = SchemaDotOrgHarvester()

        text = ir.read_text('tests.data.ieda', '600165.fixed.html')
        doc = lxml.etree.HTML(text)

        with self.assertRaises(json.decoder.JSONDecodeError):
            harvester.get_jsonld(doc)

    @patch('schema_org.core.logging.getLogger')
    def test_truncated(self, mock_logger):
        """
        SCENARIO:  The HTML file has invalid JSONLD embedded in its SCRIPT.
        The JSON is truncated, which cannot be fixed.

        EXPECTED RESULT:  An exception is raised.
        """
        harvester = SchemaDotOrgHarvester()
        text = ir.read_text('tests.data.ieda', '601015-truncated.html')
        doc = lxml.etree.HTML(text)

        with self.assertRaises(json.decoder.JSONDecodeError):
            harvester.get_jsonld(doc)

    def test_ieda_601015_over_escaped_double_quotes(self):
        """
        SCENARIO:  The HTML file has invalid JSONLD embedded in its SCRIPT.
        Two different description field have over-escaped double quotes.

        EXPECTED RESULT:  An exception is issued.
        """
        harvester = SchemaDotOrgHarvester()
        text = ir.read_text('tests.data.ieda', '601015.fixed.html')
        doc = lxml.etree.HTML(text)

        with self.assertRaises(json.decoder.JSONDecodeError):
            harvester.get_jsonld(doc)

    @aioresponses()
    def test_site_map_retrieval_failure(self, aioresp_mocker):
        """
        SCENARIO:  a non-200 status code is returned by the site map retrieval.

        EXPECTED RESULT:  A ClientResponseError is raised and the exception is
        logged.
        """
        harvester = SchemaDotOrgHarvester()

        sitemap_url = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        aioresp_mocker.get(self.regex, status=500)

        with self.assertLogs(logger=harvester.logger, level='INFO') as cm:
            with self.assertRaises(aiohttp.ClientResponseError):
                asyncio.run(harvester.get_sitemap_document(sitemap_url))

            self.assertLogMessage(
                cm.output, schema_org.core.SITEMAP_RETRIEVAL_FAILURE_MESSAGE
            )

    def test_check_if_can_be_updated(self):
        """
        SCENARIO:  The GMN existance check shows that the document has already
        been harvested.  It has been updated since the last harvest time, and
        the update succeeds.

        EXPECTED RESULT:  The update check does not error out.
        """
        host, port = 'ieda.mn.org', 443
        harvester = SchemaDotOrgHarvester(host=host, port=port)

        # This is the existing document in the MN.  It is marked as complete.
        existing_content = ir.read_binary('tests.data.ieda', '600121iso.xml')

        # This is the "update" document, same as the existing document.  It is
        # already marked as "complete" and is newer.
        docbytes = ir.read_binary('tests.data.ieda', '600121iso-later.xml')
        doi = 'doi.10000/abcde'

        current_sid = 1
        doi = 'doi.10000/abcde'

        regex = re.compile('https://ieda.mn.org:443/')
        with aioresponses() as m:
            m.get(regex, body=existing_content)
            asyncio.run(harvester.check_if_can_be_updated(docbytes, doi,
                                                          current_sid))

    def test_check_if_can_be_updated__document_is_the_same(self):
        """
        SCENARIO:  The GMN existance check shows that the document has already
        been harvested.  We have the same document on hand.

        EXPECTED RESULT:  The update check raises an exception.
        """
        host, port = 'ieda.mn.org', 443
        harvester = SchemaDotOrgHarvester(host=host, port=port)

        # This is the existing document in the MN.  It is marked as complete.
        existing_content = ir.read_binary('tests.data.ieda', '600121iso.xml')

        # This is the "update" document, same as the existing document.  It is
        # already marked as "complete" and is newer.
        docbytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        doi = 'doi.10000/abcde'
        current_sid = 1

        regex = re.compile('https://ieda.mn.org:443/')
        with aioresponses() as m:
            m.get(regex, body=existing_content)
            with self.assertRaises(schema_org.core.RefusedToUpdateRecord):
                asyncio.run(harvester.check_if_can_be_updated(docbytes, doi,
                                                              current_sid))

    def test_check_if_can_be_updated__progress_code_has_regressed(self):
        """
        SCENARIO:  The GMN existance check shows that the document has already
        been harvested.  The new document, however, is no longer complete.

        EXPECTED RESULT:  An exception is raised.
        """
        host, port = 'ieda.mn.org', 443
        harvester = SchemaDotOrgHarvester(host=host, port=port)

        # This is the existing document in the MN.  It is marked as complete.
        existing_content = ir.read_binary('tests.data.ieda', '600121iso.xml')

        # This is the "update" document, same as the existing document.  Change
        # the progress code.
        docbytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        doc = lxml.etree.parse(io.BytesIO(docbytes))
        parts = [
            'gmd:identificationInfo',
            'gmd:MD_DataIdentification',
            'gmd:status',
            'gmd:MD_ProgressCode',
        ]
        path = '/'.join(parts)
        elt = doc.xpath(path, namespaces=schema_org.core.ISO_NSMAP)[0]
        elt.text = 'in progress'

        # Re-serialize the update document.
        docbytes = lxml.etree.tostring(doc, pretty_print=True,
                                       encoding='utf-8', standalone=True)

        current_sid = 1
        doi = 'doi.10000/abcde'

        regex = re.compile('https://ieda.mn.org:443/')
        with aioresponses() as m:
            m.get(regex, body=existing_content)
            with self.assertRaises(schema_org.core.RefusedToUpdateRecord):
                asyncio.run(harvester.check_if_can_be_updated(docbytes, doi,
                                                              current_sid))

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

        EXPECTED RESULT:  The event is logged at the info level.  The update
        count increases by one.
        """
        host, port = 'ieda.mn.org', 443
        harvester = SchemaDotOrgHarvester(host=host, port=port)

        # This is the existing document in the MN.  It is marked as complete.
        existing_content = ir.read_binary('tests.data.ieda', '600121iso.xml')

        record_date = dt.datetime.now()
        mock_check_if_identifier_exists.return_value = {
            'outcome': 'yes',
            'record_date': record_date - dt.timedelta(days=1),
            'current_version_id': 1,
        }
        mock_update_science_metadata.return_value = True

        harvester = SchemaDotOrgHarvester(host=host, port=port)
        update_count = harvester.updated_count

        # This is the "update" document, same as the existing document.  It is
        # already marked as "complete".  Bump the timestamp to just a bit later
        # to make ok to proceed.
        docbytes = ir.read_binary('tests.data.ieda', '600121iso-later.xml')
        doc = lxml.etree.parse(io.BytesIO(docbytes))
        doi = 'doi.10000/abcde'

        regex = re.compile('https://ieda.mn.org:443/')
        with self.assertLogs(logger=harvester.logger, level='DEBUG') as cm:
            with aioresponses() as m:
                m.get(regex, body=existing_content)
                asyncio.run(harvester.harvest_document(doi, '1',
                                                       doc, record_date))

            # Did we see at least one information message?
            log_msg_count = self.logLevelCallCount(cm.output, level='INFO')
            self.assertTrue(log_msg_count > 1)

            # Did we increase the update count?
            self.assertEqual(harvester.updated_count, update_count + 1)

    @patch('schema_org.d1_client_manager.D1ClientManager.update_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    def test_document_already_harvested_but_fails_to_update(
        self,
        mock_check_if_identifier_exists,
        mock_update_science_metadata
    ):
        """
        SCENARIO:  The GMN existance check shows that the document has already
        been harvested.  It has been updated since the last harvest time, but
        the update failed.

        EXPECTED RESULT:  An exception is raised.
        """
        host, port = 'ieda.mn.org', 443
        harvester = SchemaDotOrgHarvester(host=host, port=port)

        # This is the existing document in the MN.  It is requested by the
        # update check, and it is marked as complete.
        existing_content = ir.read_binary('tests.data.ieda', '600121iso.xml')

        record_date = dt.datetime.now()
        mock_check_if_identifier_exists.return_value = {
            'outcome': 'yes',
            'record_date': record_date - dt.timedelta(days=1),
            'current_version_id': 1,
        }
        mock_update_science_metadata.return_value = False

        harvester = SchemaDotOrgHarvester(host=host, port=port)

        # Read a document that is the same except it has a later metadata
        # timestamp.  This means that we should update it.
        doc_bytes = ir.read_binary('tests.data.ieda', '600121iso-later.xml')
        doc = lxml.etree.parse(io.BytesIO(doc_bytes))

        doi = 'doi.10000/abcde'

        regex = re.compile('https://ieda.mn.org:443/')
        with self.assertRaises(schema_org.core.UnableToUpdateGmnRecord):
            with aioresponses() as m:
                m.get(regex, body=existing_content)
                asyncio.run(harvester.harvest_document(doi, '1',
                                                       doc, record_date))

    @patch('schema_org.d1_client_manager.D1ClientManager.update_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    @patch('schema_org.core.logging.getLogger')
    def test_document_already_harvested__followup_record_is_complete(
        self,
        mock_logger,
        mock_check_if_identifier_exists,
        mock_update_science_metadata
    ):
        """
        SCENARIO:  The GMN existance check shows that the document has already
        been harvested but has been marked as "ongoing".  It has been updated
        since the last harvest time, and the new record is marked as
        "complete".  The update succeeds.

        EXPECTED RESULT:  The updated count goes up by one and the event is
        logged at the info level.
        """
        # This is the existing document in the MN.  It is requested by the
        # update check, and it is marked as ongoing.
        existing_content = ir.read_binary('tests.data.ieda',
                                          '600121iso-ongoing.xml')

        # This is the proposed update document that is the same except it is
        # marked as complete.
        update_doc_bytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        doc = lxml.etree.parse(io.BytesIO(update_doc_bytes))

        record_date = dt.datetime.now()
        mock_check_if_identifier_exists.return_value = {
            'outcome': 'yes',
            'record_date': record_date - dt.timedelta(days=1),
            'current_version_id': 1,
        }
        mock_update_science_metadata.return_value = True

        host, port = 'ieda.mn.org', 443
        harvester = SchemaDotOrgHarvester(host=host, port=port)
        initial_updated_count = harvester.updated_count

        doi = 'doi.10000/abcde'

        regex = re.compile('https://ieda.mn.org:443/')
        with aioresponses() as m:
            m.get(regex, body=existing_content)
            asyncio.run(harvester.harvest_document(doi, '1', doc, record_date))

        # Did we increase the failure count?
        self.assertEqual(harvester.updated_count, initial_updated_count + 1)

        # Did we see a warning?
        self.assertTrue(harvester.logger.info.call_count > 0)

    @patch('schema_org.d1_client_manager.D1ClientManager.update_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    def test_document_already_harvested__followup_record_is_too_old(
        self,
        mock_check_if_identifier_exists,
        mock_update_science_metadata
    ):
        """
        SCENARIO:  The GMN existance check shows that the document has already
        been harvested.  It has been updated since the last harvest time, but
        the proposed update record is even older than the original.

        EXPECTED RESULT:  An exception is raised.
        """
        # This is the existing document in the MN.  It is requested by the
        # update check, and it is marked as complete.
        existing_content = ir.read_binary('tests.data.ieda', '600121iso.xml')

        record_date = dt.datetime.now()
        mock_check_if_identifier_exists.return_value = {
            'outcome': 'yes',
            'record_date': record_date - dt.timedelta(days=1),
            'current_version_id': 1,
        }
        mock_update_science_metadata.return_value = False

        host, port = 'ieda.mn.org', 443
        harvester = SchemaDotOrgHarvester(host=host, port=port)

        # Read a document that is the same except it has an earlier metadata
        # timestamp.  This means that we should NOT update it.
        doc_bytes = ir.read_binary('tests.data.ieda', '600121iso-earlier.xml')
        doc = lxml.etree.parse(io.BytesIO(doc_bytes))

        doi = 'doi.10000/abcde'

        regex = re.compile('https://ieda.mn.org:443/')
        with self.assertRaises(schema_org.core.RefusedToUpdateRecord):
            with aioresponses() as m:
                m.get(regex, body=existing_content)
                asyncio.run(harvester.harvest_document(doi, '1',
                                                       doc, record_date))

    @patch('schema_org.d1_client_manager.D1ClientManager.update_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    def test_document_already_harvested_at_same_date(
        self,
        mock_check_if_identifier_exists,
        mock_update_science_metadata
    ):
        """
        SCENARIO:  The GMN existance check shows that the document has already
        been harvested and has not changed since the last time.  We don't want
        to attempt to harvest in this case.

        EXPECTED RESULT:  A SkipError is raised.
        """
        record_date = dt.datetime.now()
        mock_check_if_identifier_exists.return_value = {
            'outcome': 'yes',
            'record_date': record_date,
        }
        mock_update_science_metadata.return_value = False

        harvester = SchemaDotOrgHarvester()
        docbytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        doc = lxml.etree.parse(io.BytesIO(docbytes))

        doi = 'doi.10000/abcde'

        with self.assertRaises(schema_org.core.SkipError):
            asyncio.run(harvester.harvest_document(doi, '1', doc, record_date))

    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    @patch('schema_org.core.logging.getLogger')
    def test_document_check_fails(
        self,
        mock_logger,
        mock_check_if_identifier_exists
    ):
        """
        SCENARIO:  The GMN existance check fails for some reason.

        EXPECTED RESULT:  The event is logged at the warning level.
        """
        mock_check_if_identifier_exists.return_value = {
            'outcome': 'failed',
        }

        harvester = SchemaDotOrgHarvester()
        docbytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        doc = lxml.etree.parse(io.BytesIO(docbytes))

        record_date = dt.datetime.now()

        asyncio.run(harvester.harvest_document('doi.10000/abcde', '1',
                                               doc, record_date))

        harvester.logger.warning.assert_called_once()

    @patch('schema_org.d1_client_manager.D1ClientManager.load_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    @patch('schema_org.core.logging.getLogger')
    def test_document_is_unrecognized_but_successfully_harvested(
        self,
        mock_logger,
        mock_check_if_identifier_exists,
        mock_load_science_metadata
    ):
        """
        SCENARIO:  The GMN has not seen the document before and is successfully
        harvested.

        EXPECTED RESULT:  The event is logged at the info level.  The
        "created_count" goes up by one.
        """
        mock_check_if_identifier_exists.return_value = {'outcome': 'no'}
        mock_load_science_metadata.return_value = True

        harvester = SchemaDotOrgHarvester()
        docbytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        doc = lxml.etree.parse(io.BytesIO(docbytes))

        asyncio.run(harvester.harvest_document('doi.10000/abcde',
                                               '1',
                                               doc,
                                               dt.datetime.now()))

        self.assertEqual(harvester.created_count, 1)
        harvester.logger.info.assert_called_once()

    @patch('schema_org.d1_client_manager.D1ClientManager.load_science_metadata')  # noqa: E501
    @patch('schema_org.d1_client_manager.D1ClientManager.check_if_identifier_exists')  # noqa: E501
    def test_document_is_unrecognized_but_cannot_be_harvested(
        self,
        mock_check_if_identifier_exists,
        mock_load_science_metadata
    ):
        """
        SCENARIO:  The GMN has not seen the document before, but still cannot
        harvest the document for some reason.

        EXPECTED RESULT:  An exception is raised.
        """
        mock_check_if_identifier_exists.return_value = {'outcome': 'no'}
        mock_load_science_metadata.return_value = False

        harvester = SchemaDotOrgHarvester()
        docbytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        doc = lxml.etree.parse(io.BytesIO(docbytes))

        with self.assertRaises(schema_org.core.UnableToCreateNewGMNObject):
            asyncio.run(harvester.harvest_document('doi.10000/abcde', '1',
                                                   doc,
                                                   dt.datetime.now()))

    def test_jsonld_script_found_in_body_rather_than_head(self):
        """
        SCENARIO:  The JSON-LD <SCRIPT> element is located in the <body> of the
        landing page element rather than the <head>.

        CUAHSI puts the <SCRIPT> element in the body, while ARM puts it in the
        <HEAD>.

        EXPECTED RESULT:  The JSON-LD is successfully extracted from the
        landing page document.
        """
        parts = ['tests', 'data', 'cuahsi', 'aadd7dd60f31498590de32c9b14446c3']
        package = '.'.join(parts)
        text = ir.read_text(package, 'landing_page.html')
        doc = lxml.etree.HTML(text)

        obj = SchemaDotOrgHarvester()

        with self.assertLogs(logger=obj.logger, level='DEBUG'):
            j = obj.get_jsonld(doc)

        json.dumps(j)

        self.assertTrue(True)

    def test_eml_v200(self):
        """
        SCENARIO:   Attempt to validate against a local EML v2.0.0 file.

        EXPECTED RESULT:  After validation, the formatID_custom field of the
        sys_metadict is correct for EML v2.0.
        """
        content = ir.read_binary('tests.data.eml.v2p0p0', 'example.xml')
        doc = lxml.etree.parse(io.BytesIO(content))

        obj = SchemaDotOrgHarvester()
        with self.assertLogs(logger=obj.logger, level='DEBUG'):
            obj.validate_document(doc)

        expected = "eml://ecoinformatics.org/eml-2.0.0"
        self.assertEqual(obj.sys_meta_dict['formatId_custom'], expected)

    def test_validate_fails(self):
        """
        SCENARIO:   An attempt to validate an ARM document with invalid XML is
        provided.

        EXPECTED RESULT:  An exception is issued.
        """
        content = ir.read_binary('tests.data.arm', 'nsaqcrad1longC2.c2.xml')
        doc = lxml.etree.parse(io.BytesIO(content))

        obj = SchemaDotOrgHarvester()
        with self.assertLogs(logger=obj.logger, level='DEBUG'):
            with self.assertRaises(RuntimeError):
                obj.validate_document(doc)
