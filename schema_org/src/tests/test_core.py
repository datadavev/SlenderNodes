# Standard library imports
try:
    import importlib.resources as ir
except ImportError:  # pragma:  nocover
    import importlib_resources as ir
import io
from unittest.mock import patch

# 3rd party library imports
import dateutil.parser
import lxml.etree

# local imports
from schema_org.core import CoreHarvester
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

        records = harvester.extract_records_from_sitemap(doc, last_harvest)
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

        records = harvester.extract_records_from_sitemap(doc, last_harvest)
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
            records = obj.extract_records_from_sitemap(doc, last_harvest_time)
        self.assertEqual(len(records), 3)