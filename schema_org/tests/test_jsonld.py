"""
Tests for validity of schema.org JSON-LD.
"""

# Standard library imports
import importlib.resources as ir
import json
import logging
from unittest.mock import patch

# 3rd party library imports

# Local imports
from schema_org.jsonld_validator import (
    JSONLD_Validator, JsonLdError, SOFlavor
)
from .test_common import TestCommon

XSD_DATE_MSG = (
    "A dateModified property, if present, should conform to xsd:date or "
    "xsd:datetime patterns."
)
ENCODING_FORMAT_MSG = (
    "The encodingFormat should be provided in the encoding map and must drawn "
    "from the list of DataONE formatIds to avoid ambiguity."
)


class TestSuite(TestCommon):

    def setUp(self):

        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                            level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

    def test_flavor_is_bco_dmo(self):
        """
        SCENARIO:  we have BCO-DMO-style SO content.

        EXPECTED RESULT:  The flavor is identifies as so_core.SOFlavor.BCO_DMO
        """
        v = JSONLD_Validator(logger=self.logger)

        text = ir.read_text('tests.data.bcodmo.559701', 'so.json')
        j = json.loads(text)

        flavor = v.get_so_flavor(j)
        self.assertEqual(flavor, SOFlavor.BCO_DMO)

    def test_bcodmo(self):
        """
        SCENARIO:  we have BCO-DMO-style SO content.

        EXPECTED RESULT:  It validates.
        """
        v = JSONLD_Validator(logger=self.logger)

        text = ir.read_text('tests.data.bcodmo.559701', 'so.json')
        j = json.loads(text)
        v.check(j)
        self.assertTrue(True)

    def test_flavor_is_arm(self):
        """
        SCENARIO:  we have ARM-style SO content.

        EXPECTED RESULT:  so_core.SOFlavor.ARM
        """
        v = JSONLD_Validator(logger=self.logger)

        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-02"
            }
        }
        """
        j = json.loads(s)
        flavor = v.get_so_flavor(j)
        self.assertEqual(flavor, SOFlavor.ARM)

    def test_missing_top_level_type_key(self):
        """
        SCENARIO:  The JSON-LD does not have the '@type': 'Dataset' keypair.

        EXPECTED RESULT.  A RuntimeError is issued.
        """

        content = ir.read_text('tests.data.jsonld', 'missing_dataset.json')
        j = json.loads(content)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertRaises(RuntimeError):
            v.check(j)

    def test__top_level_id_missing(self):
        """
        SCENARIO:  The JSON-LD is missing the @id entry at the top
        level.

        EXPECTED RESULT.  A RuntimeError is issued.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertRaises(RuntimeError):
            v.check(j)

    def test__top_level_id_is_not_iri(self):
        """
        SCENARIO:  The JSON-LD top level @id key is not a valid URI.  Sec 1.7
        of the JSON-LD spec seems to indicate that if it is not a "blank node"
        (that's RDF-speak), then it should be an IRI.

        EXPECTED RESULT.  An exception is issued.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertRaises(JsonLdError):
            v.check(j)

    def test__top_level_id_is_not_iri__has_leading_space(self):
        """
        SCENARIO:  The JSON-LD top level @id key is not a valid URI.  Sec 1.7
        of the JSON-LD spec seems to indicate that if it is not a "blank node"
        (that's RDF-speak), then it should be an IRI.  Here is a case where
        IEDA put a blank into the id and didn't have a scheme.

        EXPECTED RESULT.  An exception is issued.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": " dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertRaises(JsonLdError):
            v.check(j)

    def test_missing_top_level_type_dataset_keypair(self):
        """
        SCENARIO:  The JSON-LD does not have the '@type': 'Dataset' keypair.

        EXPECTED RESULT.  A RuntimeError is issued.
        """

        j = {'@context': 'https://schema.org', '@type': 'Book'}

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG'):
            with self.assertRaises(JsonLdError):
                v.check(j)

    def test_dataset_type_is_camelcase(self):
        """
        SCENARIO:  The JSON-LD has "DataSet" instead of "Dataset".

        EXPECTED RESULT.  An error is logged.
        """

        j = {'@type': 'DataSet'}

        v = JSONLD_Validator(logger=self.logger)
        with self.assertRaises(RuntimeError):
            v.check(j)

    def test_missing_top_level_encoding_keyword(self):
        """
        SCENARIO:  The JSON-LD does not have the 'encoding' keyword at the
        top level.

        EXPECTED RESULT.  An error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset"
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)
            return

            expected = "JSON-LD is missing a top-level encoding keyword."
            self.assertErrorLogMessage(cm.output, expected)

    def test__encoding__missing_contentUrl_keyword(self):
        """
        SCENARIO:  The JSON-LD does not have the 'contentUrl' keyword in the
        'encoding' block.

        EXPECTED RESULT.  An error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "description": "",
                "dateModified": "2002-04-04",
                "encodingFormat": "http://www.isotc211.org/2005/gmd"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            expected = (
                "A contentUrl entry must provide the location of the metadata "
                "encoding."
            )
            self.assertErrorLogMessage(cm.output, expected)

    def test__encoding__missing_description_keyword(self):
        """
        SCENARIO:  The JSON-LD does not have the 'description' keyword in the
        'encoding' block.

        EXPECTED RESULT.  An warning is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2004-02-02"
            },
            "identifier": {
                "@type": "PropertyValue",
                "value": "something"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            v.check(j)
            expected = 'A description property is recommended.'
            self.assertWarningLogMessage(cm.output, expected)
            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test__encoding__missing_dateModified_keyword(self):
        """
        SCENARIO:  The JSON-LD does not have the 'dateModified' keyword in the
        'encoding' block.

        EXPECTED RESULT.  An warning is logged, as dateModified is optional.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "description": ""
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            v.check(j)

            expected = (
                'A dateModified property indicating when the encoding was '
                'last updated is recommended.'
            )
            self.assertWarningLogMessage(cm.output, expected)
            self.assertErrorLogCallCount(cm.output, n=0)

    def test__encoding__dateModified_is_date(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword in the date
        format.

        EXPECTED RESULT.  No errors or warnings are logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-02"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            v.check(j)
            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test__encoding__dateModified_is_datetime(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword in the datetime
        format.

        EXPECTED RESULT.  No errors or warnings are logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-02T01:02:03"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            v.check(j)
            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test__encoding__dateModified_is_datetime_with_fractional_seconds(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword in the datetime
        format.  There are fractional seconds.

        EXPECTED RESULT.  No errors or warnings are logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-02T01:02:03.123Z"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            v.check(j)
            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test__encoding__dateModified_is_invalid_date__month_00(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  "19" is invalid.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-00-08"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, '2019-00-08')
            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_is_invalid_date__month_19(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  "19" is invalid.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-19-08"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_is_invalid_date__month_20(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  "20" is invalid.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-20-08"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_is_invalid_date__day_not_numeric(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-0A"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_is_invalid_date__invalid_day(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that has an
        invalid day of 32.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-32"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_has_invalid_hours1(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  A value of 29 is an invalid hour.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T29:59:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_has_invalid_hours2(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  A value of 31 is an invalid hour.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T31:59:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_has_invalid_minutes(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.  The minutes are invalid.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:69:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified_is_invalid_datetime__seconds(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that is not in
        a valid date or datetime format.

        EXPECTED RESULT.  A RuntimeError is raised and the error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:70"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified__leading_minus(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword in datetime
        format.  The year number is negatively signed.

        EXPECTED RESULT.  No errors reported.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "-2019-08-08T23:59:59+14:00"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            v.check(j)

            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test__encoding__dateModified__valid_zone_minute_offset(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that has a
        valid zone designator minute offset.  The minute offset includes a
        colon.

        EXPECTED RESULT.  No errors reported.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:59+14:00"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            v.check(j)

            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test__encoding__dateModified__valid_zone_designator_hour_offset(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that has a
        valid zone designator hour offset.

        EXPECTED RESULT.  No errors reported.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:59+14:00"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            v.check(j)

            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test__encoding__dateModified__zone_hhmm_edgecase(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that has a
        valid zone designator hour offset that is just outside the valid range.
        '14:00' is the absolute maximum offset.

        EXPECTED RESULT.  A RuntimeError is issued and an error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:59+14:01"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified__invalid_zone_offset_hours(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that has an
        invalid zone designator in hours.

        EXPECTED RESULT.  A RuntimeError is issued and an error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:59+25"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__encoding__dateModified__valid_zone_designator_letter(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that has a
        valid zone designator letter.  Only "Z" is allowed.

        EXPECTED RESULT.  No errors reported.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:59Z"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            v.check(j)

            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test__encoding__dateModified__invalid_zone_designator_letter(self):
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword that has an
        invalid zone designator letter.  Only "Z" is allowed.

        EXPECTED RESULT.  A RuntimeError is issued and an error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": "thing",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:59A"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)

    def test__identifier_block_missing(self):
        """
        SCENARIO:  The JSON-LD is missing the identifier section at the top
        level.

        EXPECTED RESULT.  An error is logged.
        """
        s = """
        {
            "@context": { "@vocab": "http://schema.org/" },
            "@type": "Dataset",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://somewhere.out.there.com/",
                "description": "",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-08-08T23:59:59"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)
            expected = 'A dataset must have an identifier.'
            self.assertErrorLogMessage(cm.output, expected)

    def test__encoding__dateModified_is_datetime_with_fractional_seconds_arm(self):  # noqa: E501
        """
        SCENARIO:  The JSON-LD has the 'dateModified' keyword in the datetime
        format.  There are fractional seconds.

        EXPECTED RESULT.  No errors or warnings are logged.
        """
        s = """
        {
            "@type": "Dataset",
            "@context": { "@vocab": "http://schema.org/" },
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": {
                "@type": [
                    "PropertyValue",
                    "datacite:ResourceIdentifier"
                ]
            },
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://www.archive.arm.gov/metadata.xml",
                "description": "ISO TC211 XML rendering of metadata.",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-06-24T09:04:28.886943"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            v.check(j)
            self.assertLogLevelCallCount(cm.output, level='ERROR', n=0)

    def test_inline_context(self):
        """
        SCENARIO:  The context references an inline document.  This is
        currently problematic for us and will cause errors with the
        dateModified keys.  We want to suppress this.

        EXPECTED RESULT.  No errors.
        """
        s = """
        {
            "@type": "Dataset",
            "@context": "http://schema.org",
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": {
                "@type": [
                    "PropertyValue",
                    "datacite:ResourceIdentifier"
                ]
            },
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://www.archive.arm.gov/metadata.xml",
                "description": "ISO TC211 XML rendering of metadata.",
                "encodingFormat": "http://www.isotc211.org/2005/gmd",
                "dateModified": "2019-06-24T09:04:28.886943"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        v.check(j)

        self.assertNotEqual(j['@context'], "http://schema.org")

    def test__encoding__unsupported_encoding_format(self):
        """
        SCENARIO:  The encodingFormat term in the encoding map should be a
        supported format.  "eml://ecoinformatics.org/eml-1.0.0" is not such
        a format.

        EXPECTED RESULT.  A RuntimeError is issued.  The error is logged.
        """
        s = """
        {
            "@type": "Dataset",
            "@context": { "@vocab": "http://schema.org/" },
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": {
                "@type": [
                    "PropertyValue",
                    "datacite:ResourceIdentifier"
                ]
            },
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://www.archive.arm.gov/metadata.xml",
                "description": "ISO TC211 XML rendering of metadata.",
                "dateModified": "2019-06-24T09:04:28.886943",
                "encodingFormat": "eml://ecoinformatics.org/eml-1.0.0"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, ENCODING_FORMAT_MSG)

    @patch('schema_org.jsonld_validator.Validator.run')
    def test_unexpected_pyshacl_error(self, mock_pyshacl):
        """
        SCENARIO:  pyshacl issues an exception when asked to validate some
        JSON.

        EXPECTED RESULT:  A log message detailing the error is issued at the
        WARNING level.  A RuntimeError is raised.
        """
        mock_pyshacl.side_effect = ZeroDivisionError('boom')

        s = """
        {
            "@type": "Dataset",
            "@context": { "@vocab": "http://schema.org/" },
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": {
                "@type": [
                    "PropertyValue",
                    "datacite:ResourceIdentifier"
                ]
            },
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://www.archive.arm.gov/metadata.xml",
                "description": "ISO TC211 XML rendering of metadata.",
                "dateModified": "2019-06-24T09:04:61"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertWarningLogMessage(cm.output, 'ZeroDivisionError')

    def test__two_errors(self):
        """
        SCENARIO:  The encodingFormat term is missing from the encoding map
        and the dateModified value in the encoding map is invalid.

        EXPECTED RESULT.  A RuntimeError is issued.  There are two errors
        logged.
        """
        s = """
        {
            "@type": "Dataset",
            "@context": { "@vocab": "http://schema.org/" },
            "@id": "http://dx.doi.org/10.5439/1027372",
            "identifier": {
                "@type": [
                    "PropertyValue",
                    "datacite:ResourceIdentifier"
                ]
            },
            "encoding": {
                "@type": "MediaObject",
                "contentUrl": "https://www.archive.arm.gov/metadata.xml",
                "description": "ISO TC211 XML rendering of metadata.",
                "dateModified": "2019-06-24T09:04:61"
            }
        }
        """
        j = json.loads(s)

        v = JSONLD_Validator(logger=self.logger)
        with self.assertLogs(logger=v.logger, level='DEBUG') as cm:
            with self.assertRaises(RuntimeError):
                v.check(j)

            self.assertErrorLogMessage(cm.output, ENCODING_FORMAT_MSG)
            self.assertErrorLogMessage(cm.output, XSD_DATE_MSG)
