"""
Test suite for command line tools.
"""

# Standard library imports
import contextlib
import io
import sys
from unittest.mock import patch

# Local imports
from schema_org import commandline
from .test_common import TestCommon


class TestSuite(TestCommon):

    @patch.object(sys, 'argv', ['--verbosity', 'WARNING2'])
    @patch('sys.exit')
    @patch('schema_org.commandline.ARMHarvester.run')
    @patch('schema_org.commandline.asyncio')
    def test_bad_verbosity(self, mock_asyncio, mock_arm, mock_sys_exit):
        """
        SCENARIO:  the harvester is called with a bad verbosity value.

        EXPECTED RESULT:  The command line utility will error out and try to
        exit.
        """
        with contextlib.redirect_stderr(io.StringIO()):
            # Don't mess up the terminal screen with stderr from argparse.
            commandline.arm()

        self.assertEqual(mock_sys_exit.call_count, 1)

    @patch.object(sys, 'argv', [''])
    @patch('schema_org.commandline.IEDAHarvester.run')
    @patch('schema_org.commandline.asyncio')
    def test_ieda(self, mock_asyncio, mock_ieda):
        """
        SCENARIO:  Run with no command line arguments.

        EXPECTED RESULT:  The run method was called.
        """
        commandline.ieda()

        self.assertEqual(mock_ieda.call_count, 1)

    @patch.object(sys, 'argv', [''])
    @patch('schema_org.commandline.AbdsIptHarvester.run')
    @patch('schema_org.commandline.asyncio')
    def test_abds_ipt(self, mock_asyncio, mock_abds):
        """
        SCENARIO:  Run with no command line arguments.

        EXPECTED RESULT:  The run method was called.
        """
        commandline.abds_ipt()

        self.assertEqual(mock_abds.call_count, 1)

    @patch.object(sys, 'argv', [''])
    @patch('schema_org.commandline.CUAHSIHarvester.run')
    @patch('schema_org.commandline.asyncio')
    def test_cuahsi(self, mock_asyncio, mock_cuahsi):
        """
        SCENARIO:  Run with no command line arguments.

        EXPECTED RESULT:  The run method was called.
        """
        commandline.cuahsi()

        self.assertEqual(mock_cuahsi.call_count, 1)

    @patch.object(sys, 'argv', [''])
    @patch('schema_org.commandline.NKNHarvester.run')
    @patch('schema_org.commandline.asyncio')
    def test_nkn(self, mock_asyncio, mock_nkn):
        """
        SCENARIO:  Run with no command line arguments.

        EXPECTED RESULT:  The run method was called.
        """
        commandline.nkn()

        self.assertEqual(mock_nkn.call_count, 1)

    @patch.object(sys, 'argv', [''])
    @patch('schema_org.commandline.ARMHarvester.run')
    @patch('schema_org.commandline.asyncio')
    def test_arm(self, mock_asyncio, mock_arm):
        """
        SCENARIO:  Run with no command line arguments.

        EXPECTED RESULT:  The run method was called.
        """
        commandline.arm()

        self.assertEqual(mock_arm.call_count, 1)

    @patch.object(sys, 'argv', [
        '', 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
    ])
    @patch('schema_org.commandline.D1CheckSitemap.run')
    @patch('schema_org.commandline.asyncio')
    def test_sitemap_validator(self, mock_asyncio, mock_validator):
        """
        SCENARIO:  Run the sitemap validator with a single URL for a positional
        argument.

        EXPECTED RESULT:  The validator method was called.
        """
        commandline.d1_check_site()

        self.assertEqual(mock_validator.call_count, 1)

    @patch.object(sys, 'argv', ['', 'tests/data/ieda/600121iso.xml'])
    @patch('schema_org.commandline.XMLValidator.validate')
    @patch('schema_org.commandline.asyncio')
    def test_xml_validator(self, mock_asyncio, mock_validator):
        """
        SCENARIO:  Run the XML Validator with a single file for a positional
        argument.

        EXPECTED RESULT:  The validator method was called.
        """
        commandline.validate()

        self.assertEqual(mock_validator.call_count, 1)
