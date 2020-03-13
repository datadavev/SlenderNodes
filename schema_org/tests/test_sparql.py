# Standard library imports
import datetime as dt
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
