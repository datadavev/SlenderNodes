# standard library imports
import asyncio
import importlib.resources as ir
import io
import re

# 3rd party library imports
import lxml.etree
from aioresponses import aioresponses

# local imports
import schema_org
from schema_org import D1CheckSitemap
from schema_org.core import (
    SITEMAP_RETRIEVAL_FAILURE_MESSAGE, SITEMAP_NOT_XML_MESSAGE
)
from .test_common import TestCommon


class TestSuite(TestCommon):

    def setUp(self):
        # Every URL request for ARM will match this pattern, so we set
        # aioresponses to intercept all of them.
        self.pattern = re.compile(r'https://www.archive.arm.gov/metadata/adc')

    @aioresponses()
    def test_no_site_map(self, aioresp_mocker):
        """
        SCENARIO:  The given URL for the sitemap does not seem to exist.

        EXPECTED RESULT:  Errors are recorded.
        """
        aioresp_mocker.get(self.pattern, status=400)

        sitemap = 'https://www.archive.arm.gov/metadata/adc/sitemap.txt'
        obj = D1CheckSitemap(sitemap_url=sitemap, verbosity='DEBUG')
        with self.assertLogs(logger=obj.logger, level='INFO') as cm:
            asyncio.run(obj.run())

            msgs = [SITEMAP_RETRIEVAL_FAILURE_MESSAGE, 'ClientResponseError']
            self.assertLogMessage(cm.output, msgs)

    @aioresponses()
    def test_landing_page_is_not_present(self, aioresp_mocker):
        """
        SCENARIO:  The sitemap references two documents.  The first landing
        page document that is not present, but the next one is fine.

        EXPECTED RESULT:  The log record reflects the successful calls, but
        also failure to retrieve the HTML.
        """

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1 (fails)
        #   3) HTML document for record 2
        #   4) XML document for record 2
        #
        contents = [
            ir.read_text('tests.data.arm', 'sitemap2.xml'),
            b'',
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.xml'),
        ]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
        ]
        status_codes = [200, 400, 200, 200]

        for content, header, status in zip(contents, headers, status_codes):
            aioresp_mocker.get(self.pattern, body=content, headers=header,
                               status=status)

        sitemap = 'https://www.archive.arm.gov/metadata/adc/sitemap_not.xml'
        obj = D1CheckSitemap(sitemap_url=sitemap)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())

            self.assertErrorLogMessage(cm.output, "Bad Request")
            self.assertSuccessfulDebugIngest(cm.output)

    @aioresponses()
    def test_jsonld_script_elemement_is_not_valid_json(self, aioresp_mocker):
        """
        SCENARIO:  The sitemap references two documents.  The first landing
        page document has a JSON-LD script element that is not valid JSON-LD.
        The 2nd document is good.

        EXPECTED RESULT:  The log records the JSON-LD failure, but also the
        successful ingest of the 2nd document.
        """

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1 (no XML document can be accessed)
        #   3) HTML document for record 2
        #   4) XML document for record 2
        #
        contents = [
            ir.read_text('tests.data.arm', 'sitemap2.xml'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.invalid_jsonld.html'),  # noqa: E501
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.xml'),
        ]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
        ]

        for header, content in zip(headers, contents):
            aioresp_mocker.get(self.pattern, headers=header, body=content)

        sitemap = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        obj = D1CheckSitemap(sitemap_url=sitemap)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())

            self.assertErrorLogMessage(cm.output, 'JSONDecodeError')
            self.assertSuccessfulDebugIngest(cm.output)

    @aioresponses()
    def test_jsonld_script_elemement_is_missing_the_id(self, aioresp_mocker):
        """
        SCENARIO:  The sitemap references two documents.  The first landing
        page document has a JSON-LD script element that is missing the ID.
        The 2nd document is good.

        EXPECTED RESULT:  The log records the JSON-LD failure, but also the
        successful ingest of the 2nd document.
        """

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1 (no XML document will be accessed)
        #   3) HTML document for record 2
        #   4) XML document for record 2
        #
        contents = [
            ir.read_text('tests.data.arm', 'sitemap2.xml'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.missing_id.html'),  # noqa: E501
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.xml'),
        ]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
        ]

        for header, content in zip(headers, contents):
            aioresp_mocker.get(self.pattern, headers=header, body=content)

        url = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        obj = D1CheckSitemap(sitemap_url=url)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())

            self.assertErrorLogMessage(cm.output, '@id')
            self.assertSuccessfulDebugIngest(cm.output)

    @aioresponses()
    def test_xml_metadata_document_is_missing(self, aioresp_mocker):
        """
        SCENARIO:  The sitemap references two documents.  The first landing
        page document references an XML document that is not present.  The 2nd
        document is good.

        EXPECTED RESULT:  The log records the XML retrieval failure,
        but also the successful ingest of the 2nd document.
        """

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) XML document for record 1 (fails)
        #   3) HTML document for record 2
        #   4) XML document for record 2
        #
        contents = [
            ir.read_binary('tests.data.arm', 'sitemap2.xml'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.html'),
            b'',
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.xml'),
        ]
        status_codes = [200, 200, 400, 200, 200]
        headers = [
            {'Content-Type': 'text/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'text/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'text/xml'},
        ]
        z = zip(contents, status_codes, headers)
        for content, status_code, headers in z:
            aioresp_mocker.get(self.pattern,
                               body=content,
                               status=status_code,
                               headers=headers)

        url = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        obj = D1CheckSitemap(sitemap_url=url)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())

            self.assertErrorLogMessage(cm.output, "Bad Request")
            self.assertSuccessfulDebugIngest(cm.output)

    @aioresponses()
    def test_metadata_document_is_invalid_xml(self, aioresp_mocker):
        """
        SCENARIO:  The sitemap references two documents.  The first landing
        page document references an XML document that is not valid XML.  The
        2nd document is good.

        EXPECTED RESULT:  The log records the invalid XML for the first
        document, but also the successful ingest of the 2nd document.
        """

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) XML document for record 1
        #   3) HTML document for record 2
        #   4) XML document for record 2
        #
        contents = [
            ir.read_text('tests.data.arm', 'sitemap2.xml'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.html'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.invalid.xml'),
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.xml'),  # noqa: E501
        ]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
        ]
        for header, content in zip(headers, contents):
            aioresp_mocker.get(self.pattern, headers=header, body=content)

        url = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        obj = D1CheckSitemap(sitemap_url=url)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())

            self.assertLogMessage(cm.output, 'XMLMetadataParsingError')
            self.assertSuccessfulDebugIngest(cm.output)

    @aioresponses()
    def test_metadata_document_does_not_validate(self, aioresp_mocker):
        """
        SCENARIO:  The sitemap references two documents.  The first landing
        page document references an XML document that does not validate.  The
        2nd document is good.

        EXPECTED RESULT:  The successful ingest of the 2nd document is
        reflected in the log.  The validation failure is also reflected,
        specifically the identity of the CI_Responsibility element.
        """

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) XML document for record 1
        #   3) HTML document for record 2
        #   4) XML document for record 2
        #
        contents = [
            ir.read_text('tests.data.arm', 'sitemap2.xml'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.html'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.xml'),
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.xml'),
        ]
        headers = [
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
        ]
        for header, content in zip(headers, contents):
            aioresp_mocker.get(self.pattern, headers=header, body=content)

        url = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        obj = D1CheckSitemap(sitemap_url=url)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())

            expected_msgs = [
                'XML document does not validate', 'CI_ResponsibleParty'
            ]
            self.assertLogMessage(cm.output, expected_msgs)
            self.assertSuccessfulDebugIngest(cm.output)

    @aioresponses()
    def test_sitemap_is_gzipped(self, aioresp_mocker):
        """
        SCENARIO:  The sitemap references two documents, both of which are
        good.  The sitemap is gzipped.

        EXPECTED RESULT:  The successful ingest of both documents is logged.
        """

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) XML document for record 1
        #   3) HTML document for record 2
        #   4) XML document for record 2
        #
        contents = [
            ir.read_binary('tests.data.arm', 'sitemap2.xml.gz'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.html'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.xml'),
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.xml'),
        ]
        headers = [
            {'Content-Type': 'application/x-gzip'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
        ]

        for header, content in zip(headers, contents):
            aioresp_mocker.get(self.pattern, headers=header, body=content)

        url = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        obj = D1CheckSitemap(sitemap_url=url)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())
            self.assertSuccessfulDebugIngest(cm.output, n=2)

    @aioresponses()
    def test_sitemap_url_is_sitemap_index_file(self, aioresp_mocker):
        """
        SCENARIO:  The URL given is actually a sitemap index that references
        two sitemaps.  Both sitemaps have two documents that are both good.

        EXPECTED RESULT:  The successful ingest of all four documents is
        logged.
        """

        # External calls to read the:
        #
        #   1) sitemap index file
        #   2) sitemap 1
        #   3) HTML document for record 1
        #   4) XML document for record 1
        #   5) HTML document for record 2
        #   6) XML document for record 2
        #   7) sitemap 2
        #   8) HTML document for record 1
        #   9) XML document for record 1
        #   10) HTML document for record 2
        #   11) XML document for record 2
        #
        contents = [
            ir.read_text('tests.data.arm', 'sitemap_index_file.xml'),

            ir.read_binary('tests.data.arm', 'sitemap2.xml.gz'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.html'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.xml'),
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.xml'),  # noqa: E501

            ir.read_binary('tests.data.arm', 'sitemap2.xml.gz'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.html'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.xml'),
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.xml'),  # noqa: E501
        ]
        header_types = [
            'application/xml',

            'application/x-gzip',
            'text/html',
            'application/xml',
            'text/html',
            'application/xml',

            'application/x-gzip',
            'text/html',
            'application/xml',
            'text/html',
            'application/xml',
        ]
        for header, content in zip(header_types, contents):
            aioresp_mocker.get(self.pattern, headers={'Content-Type': header},
                               body=content)

        url = 'https://www.archive.arm.gov/metadata/adc/sitemap_index_file.xml'
        obj = D1CheckSitemap(sitemap_url=url)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())

            self.assertSuccessfulDebugIngest(cm.output, n=4)

    @aioresponses()
    def test_site_map_is_not_xml(self, aioresp_mocker):
        """
        SCENARIO:  The sitemap document is not XML.

        EXPECTED RESULT:  There is an error stating that the URL may not be
        XML, plus an XMLSyntaxError is raised.
        """
        content = ir.read_text('tests.data.arm', 'sitemap.txt')
        headers = {'Content-Type': 'text/plain'}
        aioresp_mocker.get(self.pattern, body=content, headers=headers)

        url = 'https://www.archive.arm.gov/metadata/adc/sitemap.txt'
        obj = D1CheckSitemap(sitemap_url=url)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())

            # Verify the warning about the sitemap possibly not being XML.
            self.assertLogMessage(cm.output, SITEMAP_NOT_XML_MESSAGE,
                                  level='WARNING')

            # Verify the exception caught when trying to parse the sitemap.
            self.assertLogMessage(cm.output, 'XMLSyntaxError', level='ERROR')

    @aioresponses()
    def test_limit_number_of_documents(self, aioresp_mocker):
        """
        SCENARIO:  We do not wish to go through the entire list of documents,
        so a limit is specified.  There are 3 records in the sitemap, only 2
        are to be processed.

        EXPECTED RESULT:  Three records are detected in the sitemap, but the
        log shows only two were processed.
        """
        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) XML document for record 1
        #   3) HTML document for record 2
        #   4) XML document for record 2
        #
        contents = [
            ir.read_binary('tests.data.arm', 'sitemap3.xml'),
            ir.read_binary('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.html'),
            ir.read_binary('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.xml'),
            ir.read_binary('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_binary('tests.data.arm', 'nsasondewnpnS01.b1.fixed.xml'),
        ]
        headers = [
            {'Content-Type': 'text/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'text/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'text/xml'},
        ]
        for content, headers in zip(contents, headers):
            aioresp_mocker.get(self.pattern, body=content, headers=headers)

        url = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        obj = D1CheckSitemap(sitemap_url=url, num_documents=2)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())

            # Only two records processed.
            self.assertSuccessfulDebugIngest(cm.output, n=2)

        # And just to show, there are 3 URLs in the sitemap.
        doc = lxml.etree.parse(io.BytesIO(contents[0]))
        urls = doc.xpath('.//sm:loc/text()',
                         namespaces=schema_org.core.SITEMAP_NS)
        self.assertEqual(len(urls), 3)

    @aioresponses()
    def test_multiple_workers(self, aioresp_mocker):
        """
        SCENARIO:  The sitemap references two documents, both of which are
        good.  More than one worker is employed.  Warning, this test seems
        brittle.

        EXPECTED RESULT:  The successful ingest of both documents is logged.
        Tasks can be seen as being created for both workers.  There should be
        a log message stating that two records were successfully processed.
        """

        # External calls to read the:
        # Have to have a lot of documents because just two might not be enough
        # to get more than one worker involved.
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) XML document for record 1
        #   3) HTML document for record 2
        #   4) XML document for record 2
        #
        contents = [
            ir.read_text('tests.data.arm', 'sitemap2.xml'),

            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.html'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.xml'),
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.xml'),
        ]
        headers = [
            {'Content-Type': 'application/x-gzip'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'application/xml'},
        ]
        for header, content in zip(headers, contents):
            aioresp_mocker.get(self.pattern, headers=header, body=content)

        url = 'https://www.archive.arm.gov/metadata/adc/sitemap2.xml'
        obj = D1CheckSitemap(sitemap_url=url, num_workers=2)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())
            self.assertSuccessfulDebugIngest(cm.output, n=2)

            # If there was more than one worker, then there should be messages
            # logged that have the strings "consume(0)" and "consume(1)".
            expected_msgs = [
                f"create task for sitemap_consumer[{idx}]"
                for idx in range(2)
            ]
            self.assertLogMessage(cm.output, expected_msgs, level='DEBUG')

            expected = 'Successfully processed 2 records'
            self.assertInfoLogMessage(cm.output, expected)

    @aioresponses()
    def test__max_num_errors(self, aioresp_mocker):
        """
        SCENARIO:  The sitemap references several documents, one of which
        has invalid XML.  The max_num_errors setting has been lowered to one,
        which should trigger a shutdown.

        EXPECTED RESULT:  We should stop processing as soon as that first
        error is encountered.  There should be an INFO shutdown message.
        """

        # External calls to read the:
        #
        #   1) sitemap
        #   2) HTML document for record 1
        #   3) XML document for record 1
        #   3) HTML document for record 2
        #   4) XML document for record 2
        #
        contents = [
            ir.read_text('tests.data.arm', 'sitemap2.xml'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.fixed.html'),
            ir.read_text('tests.data.arm', 'nsaqcrad1longC2.c2.invalid.xml'),
            ir.read_text('tests.data.arm', 'nsasondewnpnS01.b1.fixed.html'),
            ir.read_text('tests.data.arm', 'nsanimfraod1michC2.c1.fixed.xml'),  # noqa: E501
        ]
        status_codes = [200, 200, 200, 200, 200]
        headers = [
            {'Content-Type': 'text/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'text/xml'},
            {'Content-Type': 'text/html'},
            {'Content-Type': 'text/xml'},
        ]
        z = zip(contents, status_codes, headers)
        for content, status_code, headers in z:
            aioresp_mocker.get(self.pattern,
                               body=content,
                               status=status_code,
                               headers=headers)

        url = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        obj = D1CheckSitemap(sitemap_url=url, max_num_errors=1)

        with self.assertLogs(logger=obj.logger, level='DEBUG') as cm:
            asyncio.run(obj.run())

            self.assertInfoLogMessage(cm.output, 'Shutting down')
