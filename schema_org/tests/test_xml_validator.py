"""
Test suite for the XML validation
"""
# Standard library imports
try:
    import importlib.resources as ir
except ImportError:  # pragma:  nocover
    import importlib_resources as ir
import io
import pathlib
import unittest

# 3rd party library imports
import lxml.etree

# Local imports
from schema_org.xml_validator import XMLValidator
from .test_common import TestCommon


class TestSuite(TestCommon):

    def test_file_like_object(self):
        """
        SCENARIO:   A file on the local file system is passed into the
        validator.  The file contains valid ISO 19115 metadata.

        SCENARIO:  no errors
        """
        validator = XMLValidator()

        content = ir.read_binary('tests.data.ieda', '600121iso.xml')
        file = io.BytesIO(content)

        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(file)

            gmd = 'http://www.isotc211.org/2005/gmd'
            self.assertLogMessage(cm.output, gmd, level='INFO')

    def test_element_tree(self):
        """
        SCENARIO:   An ElementTree is passed into the validator.  The document
        is valid ISO 19115 metadata.

        SCENARIO:  Validates.
        """
        validator = XMLValidator()

        content = ir.read_binary('tests.data.arm',
                                 'nsanimfraod1michC2.c1.fixed.xml')
        doc = lxml.etree.parse(io.BytesIO(content))

        gmd = 'http://www.isotc211.org/2005/gmd'
        gmd_noaa = 'http://www.isotc211.org/2005/gmd-noaa'

        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(doc)

            self.assertLogMessage(cm.output, gmd, level='INFO')
            self.assertLogMessage(cm.output, gmd_noaa, level='INFO')

    # @unittest.skip('cannot validate just yet')
    def test_bcodmo(self):
        """
        SCENARIO:   A valid BCODMO file is given.

        SCENARIO:  Validates to noaa gmd.
        """
        validator = XMLValidator()

        path = pathlib.Path('tests/data/bcodmo/67937/isometadata.xml')

        gmd_noaa = 'http://www.isotc211.org/2005/gmd-noaa'

        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(path, format_id=gmd_noaa)

            self.assertErrorLogCallCount(cm.output, n=0)
            self.assertLogMessage(cm.output, gmd_noaa, level='INFO')

    def test_file(self):
        """
        SCENARIO:   A valid pathlib.Path object is passed into the
        validator.  The file contains valid ISO 19115 metadata.

        SCENARIO:  Validates to regular gmd.
        """
        validator = XMLValidator()

        path = str(pathlib.Path('tests/data/ieda/600121iso.xml'))

        gmd = 'http://www.isotc211.org/2005/gmd'
        gmd_noaa = 'http://www.isotc211.org/2005/gmd-noaa'

        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(path)

            self.assertLogMessage(cm.output, gmd, level='INFO')
            self.assertLogMessage(cm.output, gmd_noaa, level='INFO')

    def test_path(self):
        """
        SCENARIO:   A valid pathlib.Path object is passed into the
        validator.  The file contains valid ISO 19115 metadata.

        SCENARIO:  Validates to regular gmd.
        """
        validator = XMLValidator()

        path = pathlib.Path('tests/data/ieda/600121iso.xml')

        gmd = 'http://www.isotc211.org/2005/gmd'
        gmd_noaa = 'http://www.isotc211.org/2005/gmd-noaa'

        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(path)

            self.assertLogMessage(cm.output, gmd, level='INFO')
            self.assertLogMessage(cm.output, gmd_noaa, level='INFO')

    def test_url(self):
        """
        SCENARIO:   A valid URL of a valid XML document is provided.

        EXPECTED RESULT:  no errors
        """
        content = ir.read_binary('tests.data.arm',
                                 'nsanimfraod1michC2.c1.fixed.xml')
        url = 'https://www.acme.org/nsanimfraod1michC2.c1.fixed.xml'

        validator = XMLValidator()

        contents = [content]
        self.setUpRequestsMocking(validator, contents=contents)

        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(url)

            self.assertErrorLogCallCount(cm.output, n=0)

    def test_invalid_url(self):
        """
        SCENARIO:   An invalid URL is provided.  A HTTP code 400 results.

        EXPECTED RESULT:  The HTTP error is logged.  No exception is
        propagated, though.
        """
        validator = XMLValidator()

        self.setUpRequestsMocking(validator, status_codes=[400])

        with self.assertLogs(logger=validator.logger, level='DEBUG') as cm:
            validator.validate('https://www.acme.org/a.xml')

            self.assertDebugLogMessage(cm.output, 'HTTPError')
            self.assertErrorLogMessage(cm.output, '400 Client Error')

    def test_file_like_object_but_invalid_xml(self):
        """
        SCENARIO:   A file on the local file system is passed into the
        validator.  The file contains invalid XML, which is invalid even before
        one starts to consider metadata standards.

        EXPECTED RESULT:  An lxml XMLSyntaxError is detected at the DEBUG
        level, with the text of the error showing up at the ERROR level.
        """
        validator = XMLValidator()

        content = ir.read_binary('tests.data.arm', 'nsanimfraod1michC2.c1.xml')
        file = io.BytesIO(content)

        with self.assertLogs(logger=validator.logger, level='DEBUG') as cm:
            validator.validate(file)
            self.assertLogMessage(cm.output, 'XMLSyntaxError', level='DEBUG')
            self.assertLogMessage(cm.output, 'xmlParseEntityRef: no name',
                                  level='ERROR')

    def test_scimeta_error(self):
        """
        SCENARIO:   A file on the local file system is passed into the
        validator.  The file

        EXPECTED RESULT:  A d1_validate.SciMetaError is detected.
        """
        validator = XMLValidator()

        content = ir.read_binary('tests.data.arm', 'nsasondewnpnS01.b1.xml')
        file = io.BytesIO(content)

        with self.assertLogs(logger=validator.logger, level='DEBUG') as cm:
            validator.validate(file)
            self.assertLogMessage(cm.output, 'SciMetaError', level='DEBUG')
            self.assertLogMessage(cm.output, 'XML document does not validate',
                                  level='ERROR')

    def test_local_eml_v200(self):
        """
        SCENARIO:   Run the validator against a local EML v2.0.0 file.  The
        DOI is doi:10.5063/AA/knb.165.2.

        EXPECTED RESULT:  Validates to "eml://ecoinformatics.org/eml-2.0.0.
        """
        content = ir.read_binary('tests.data.eml.v2p0p0', 'example.xml')
        file = io.BytesIO(content)

        validator = XMLValidator()
        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(file)

            expected = "eml://ecoinformatics.org/eml-2.0.0"
            self.assertLogMessage(cm.output, expected, level='INFO')
            self.assertErrorLogCallCount(cm.output, n=0)

    def test_local_eml_file(self):
        """
        SCENARIO:   Run the validator against a local EML v2.1.1 file

        EXPECTED RESULT:  no errors
        """
        content = ir.read_binary('tests.data.eml.v211', 'example.xml')
        file = io.BytesIO(content)

        validator = XMLValidator()
        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(file)

            expected = "eml://ecoinformatics.org/eml-2.1.1"
            self.assertLogMessage(cm.output, expected, level='INFO')
            self.assertErrorLogCallCount(cm.output, n=0)

    def test_local_pangaea_file(self):
        """
        SCENARIO:   Run the validator against a local Pangaea XML file.

        EXPECTED RESULT:  no errors
        """
        content = ir.read_binary('tests.data.pangaea',
                                 '10p1594_pangaea.729391.xml')
        file = io.BytesIO(content)

        validator = XMLValidator()
        expected = "http://www.isotc211.org/2005/gmd-pangaea"

        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(file)

            self.assertLogMessage(cm.output, expected, level='INFO')
            self.assertErrorLogCallCount(cm.output, n=0)

    def test_local_dryad_v3p1(self):
        """
        SCENARIO:   Run the validator against a local dryad file.

        EXPECTED RESULT: The format ID is http://datadryad.org/profile/v3.1
        """
        content = ir.read_binary('tests.data.dryad.v3p1', 'example.xml')
        file = io.BytesIO(content)

        validator = XMLValidator()

        with self.assertLogs(logger=validator.logger, level='INFO') as cm:

            validator.validate(file)

            for expected in [
                'http://datadryad.org/profile/v3.1',
                'http://purl.org/dryad/terms/'
            ]:
                self.assertLogMessage(cm.output, expected, level='INFO')
            self.assertErrorLogCallCount(cm.output, n=0)

    def test_local_gmd_noaa(self):
        """
        SCENARIO:   Run the validator against a local GMD NOAA file.

        EXPECTED RESULT: It validates to regular gmd, but will also validate to
        gmd-noaa.
        """
        content = ir.read_binary('tests.data.gmd_noaa', 'example.xml')
        file = io.BytesIO(content)

        expected = [
            'http://www.isotc211.org/2005/gmd',
            'http://www.isotc211.org/2005/gmd-noaa'
        ]

        validator = XMLValidator()
        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(file)

            for item in expected:
                self.assertLogMessage(cm.output, expected, level='INFO')
            self.assertErrorLogCallCount(cm.output, n=0)

    def test_local_eml_v2p1p0(self):
        """
        SCENARIO:   Run the validator against a local EML v2.0.1 file.

        EXPECTED RESULT: The format ID is eml://ecoinformatics.org/eml-2.0.1
        """
        content = ir.read_binary('tests.data.eml.v2p0p1', 'example.xml')
        file = io.BytesIO(content)

        validator = XMLValidator()
        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(file)

            expected = 'eml://ecoinformatics.org/eml-2.0.1'
            self.assertLogMessage(cm.output, expected, level='INFO')
            self.assertErrorLogCallCount(cm.output, n=0)

    def test_local_onedcx_v1p0(self):
        """
        SCENARIO:   Run the validator against a local DataONE Dublin Core
        Extended v1.0 file.

        EXPECTED RESULT: The format ID is
        http://ns.dataone.org/metadata/schema/onedcx/v1.0
        """
        content = ir.read_binary('tests.data.onedcx.v1p0', 'example.xml')
        file = io.BytesIO(content)

        validator = XMLValidator()

        expected = 'http://ns.dataone.org/metadata/schema/onedcx/v1.0'
        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(file)
            self.assertLogMessage(cm.output, expected, level='INFO')
            self.assertErrorLogCallCount(cm.output, n=0)

    def test_local_oai_2p0_oai_dc(self):
        """
        SCENARIO:   Run the validator against a local OAI-PMH Dublin
        Core v2.0, with online related resource file.

        EXPECTED RESULT: The format ID is
        http://www.openarchives.org/OAI/2.0/oai_dc/
        """
        content = ir.read_binary('tests.data.oai.2p0.oai_dc', 'example.xml')
        file = io.BytesIO(content)

        expected = 'http://www.openarchives.org/OAI/2.0/oai_dc/'

        validator = XMLValidator()
        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(file)
            self.assertLogMessage(cm.output, expected, level='INFO')
            self.assertErrorLogCallCount(cm.output, n=0)

    def test__local_oai_2p0_oai_dc__specific_id(self):
        """
        SCENARIO:   Run the validator against a local OAI-PMH Dublin
        Core v2.0, with online related resource file.  We specify the format
        ID.

        EXPECTED RESULT: The format ID is
        http://www.openarchives.org/OAI/2.0/oai_dc/
        """
        content = ir.read_binary('tests.data.oai.2p0.oai_dc', 'example.xml')
        file = io.BytesIO(content)

        expected = 'http://www.openarchives.org/OAI/2.0/oai_dc/'

        validator = XMLValidator()
        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(file, format_id=expected)
            self.assertLogMessage(cm.output, expected, level='INFO')
            self.assertErrorLogCallCount(cm.output, n=0)

    def test__waterml_v1p1(self):
        """
        SCENARIO:   Run the validator against a local WaterML file.  We don't
        support that yet.  Try to validate it as
        http://www.openarchives.org/OAI/2.0/oai_dc/ , which it is not.

        EXPECTED RESULT:  The error is logged.
        """
        content = ir.read_binary('tests.data.waterML.v1p1', 'example.xml')
        file = io.BytesIO(content)

        expected = (
            'No matching global declaration available for the validation root.'
        )

        validator = XMLValidator()
        with self.assertLogs(logger=validator.logger, level='INFO') as cm:
            validator.validate(file, format_id=expected)
            self.assertErrorLogMessage(cm.output, expected)
