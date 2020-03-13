# Standard library imports
import datetime as dt
import importlib.resources as ir
import unittest

# 3rd party library imports

# local imports
from schema_org import sotools


class TestSuite(unittest.TestCase):

    def test_dateModified_top_level(self):
        """
        SCENARIO:  We have JSON-LD with dateModified in the top level dataset
        element.

        EXPECTED RESULT:  lastModified is extracted
        """
        s = """
        {
           "@id":"ds_m_encoding",
           "@context": {
               "@vocab": "https://schema.org/"
           },
           "@type":"Dataset",
           "dateModified":"2019-10-10T12:43:11.12345",
           "encoding": {
               "@id":"ds_m_encoding#media-object",
               "@type":"MediaObject",
               "contentUrl":"https://my.server.net/datasets/00.xml",
               "description":"ISO TC211 XML rendering of metadata",
               "encodingFormat":"http://www.isotc211.org/2005/gmd"
           }
        }
        """
        data = s.encode('utf-8')

        g = sotools.common.loadSOGraph(data=data)
        actual = sotools.common.getDateModified(g)
        expected = dt.datetime(2019, 10, 10, 12, 43, 11, 123450,
                               tzinfo=dt.timezone.utc)
        self.assertEqual(actual, expected)

    def test_dateModified_in_encoding(self):
        """
        SCENARIO:  We have JSON-LD with dateModified in the encoding element.

        EXPECTED RESULT:  lastModified is extracted
        """
        s = """
        {
           "@id":"ds_m_encoding",
           "@context": {
               "@vocab": "https://schema.org/"
           },
           "@type":"Dataset",
           "encoding": {
               "@id":"ds_m_encoding#media-object",
               "@type":"MediaObject",
               "contentUrl":"https://my.server.net/datasets/00.xml",
               "dateModified":"2019-12-10T12:43:11.12345",
               "description":"ISO TC211 XML rendering of metadata",
               "encodingFormat":"http://www.isotc211.org/2005/gmd"
           }
        }
        """
        data = s.encode('utf-8')

        g = sotools.common.loadSOGraph(data=data)
        actual = sotools.common.getDateModified(g)
        expected = dt.datetime(2019, 12, 10, 12, 43, 11, 123450,
                               tzinfo=dt.timezone.utc)
        self.assertEqual(actual, expected)

    def test_dateModified_in_both_encoding_and_dataset(self):
        """
        SCENARIO:  We have JSON-LD with dateModified in both encoding element
        and in the dataset element

        EXPECTED RESULT:  lastModified from the encoding element is selected
        """
        s = """
        {
           "@id":"ds_m_encoding",
           "@context": {
               "@vocab": "https://schema.org/"
           },
           "@type":"Dataset",
           "dateModified":"2020-12-10T12:43:11.12345",
           "encoding": {
               "@id":"ds_m_encoding#media-object",
               "@type":"MediaObject",
               "contentUrl":"https://my.server.net/datasets/00.xml",
               "dateModified":"2019-12-10T12:43:11.12345",
               "description":"ISO TC211 XML rendering of metadata",
               "encodingFormat":"http://www.isotc211.org/2005/gmd"
           }
        }
        """
        data = s.encode('utf-8')

        g = sotools.common.loadSOGraph(data=data)
        actual = sotools.common.getDateModified(g)
        expected = dt.datetime(2019, 12, 10, 12, 43, 11, 123450,
                               tzinfo=dt.timezone.utc)
        self.assertEqual(actual, expected)

    def test_dateModified_in_neither_encoding_nor_dataset(self):
        """
        SCENARIO:  We have JSON-LD with dateModified in neither the encoding
        element nor the dataset element.

        EXPECTED RESULT:  RuntimeError
        """
        s = """
        {
           "@id":"ds_m_encoding",
           "@context": {
               "@vocab": "https://schema.org/"
           },
           "@type":"Dataset",
           "encoding": {
               "@id":"ds_m_encoding#media-object",
               "@type":"MediaObject",
               "contentUrl":"https://my.server.net/datasets/00.xml",
               "description":"ISO TC211 XML rendering of metadata",
               "encodingFormat":"http://www.isotc211.org/2005/gmd"
           }
        }
        """
        data = s.encode('utf-8')

        g = sotools.common.loadSOGraph(data=data)
        actual = sotools.common.getDateModified(g)
        self.assertIsNone(actual)

    def test__arm__getDatasetMetadataLinksFromSubjectOf(self):
        """
        SCENARIO:  We have JSON-LD with ARM metadata.

        EXPECTED RESULT: the contentUrl, subjectOf (ID), encodingFormat, and
        dateModified are extracted as expected.
        """
        html = ir.read_text('tests.data.arm', 'wsacrcrcal.html')
        landing_page_url = 'https://www.archive.arm.gov/metadata/adc/html/wsacrcrcal.html'
        g = sotools.common.loadSOGraphFromHtml(html, landing_page_url)
        mlinks = sotools.common.getDatasetMetadataLinks(g)

        expected = 'https://www.archive.arm.gov/metadata/adc/xml/wsacrcrcal.xml'
        self.assertEqual(mlinks[0]['contentUrl'], expected)

        expected = "http://dx.doi.org/10.5439/1150280"
        self.assertEqual(mlinks[0]['subjectOf'], expected)

        expected = "2019-11-25T16:00:21.746316"
        self.assertEqual(str(mlinks[0]['dateModified']), expected)

        expected = "http://www.isotc211.org/2005/gmd"
        self.assertEqual(str(mlinks[0]['encodingFormat']), expected)

    def test__bcodmo__getDatasetMetadataLinksFromSubjectOf(self):
        """
        SCENARIO:  We have JSON-LD with BCO-DMO metadata.

        EXPECTED RESULT: the contentUrl, subjectOf (ID), encodingFormat, and
        dateModified are extracted as expected.
        """
        html = ir.read_text('tests.data.bcodmo.559701', 'landing_page.html')
        landing_page_url = 'https://www.bco-dmo.org/dataset/559701'
        g = sotools.common.loadSOGraphFromHtml(html, landing_page_url)
        mlinks = sotools.common.getDatasetMetadataLinks(g)

        expected = 'https://www.bco-dmo.org/dataset/559701/iso'
        self.assertEqual(mlinks[0]['contentUrl'], expected)

        expected = "https://www.bco-dmo.org/dataset/559701"
        self.assertEqual(mlinks[0]['subjectOf'], expected)

        self.assertIsNone(mlinks[0]['dateModified'])

        actual = mlinks[0]['encodingFormat']
        expected = 'http://www.isotc211.org/2005/gmd-noaa'
        self.assertEqual(actual, expected)

    def test__generic__getDatasetMetadataLinksFromSubjectOf(self):
        """
        SCENARIO:  We have JSON-LD with generic metadata.

        EXPECTED RESULT: the contentUrl, subjectOf (ID), encodingFormat, and
        dateModified are extracted as expected.
        """
        html = ir.read_text('tests.data.generic', 'landing_page.html')
        landing_page_url = 'https://my.server.net/data/'
        g = sotools.common.loadSOGraphFromHtml(html, landing_page_url)
        mlinks = sotools.common.getDatasetMetadataLinks(g)

        expected = 'https://my.server.org/data/ds-02/metadata.xml'
        self.assertEqual(mlinks[0]['contentUrl'], expected)

        expected = 'https://my.server.net/data/ds-02'
        self.assertEqual(mlinks[0]['subjectOf'], expected)

        self.assertIsNone(mlinks[0]['dateModified'])

        actual = set([mlinks[0]['encodingFormat'],
                      mlinks[1]['encodingFormat']])
        expected = set(['None',
                        'http://ns.dataone.org/metadata/schema/onedcx/v1.0'])
        self.assertEqual(actual, expected)
