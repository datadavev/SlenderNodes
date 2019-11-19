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
from unittest.mock import patch

# Local imports
from schema_org.xml_validator import XMLValidator
from .test_common import TestCommon, MockRequestsResponse


class TestSuite(TestCommon):

    def setup_requests_patcher(self, contents=None, status_codes=None):
        """
        Mock out the outcome of calling 'requests.Session.get'
        """
        if contents is None and status_codes is None:
            msg = 'not both contents and status_codes can be none.'
            raise RuntimeError(msg)

        # But if only "contents" was provided, assume all the status codes
        # are good.
        if status_codes is None:
            status_codes = [200 for item in contents]

        if contents is None:
            contents = [None for item in status_codes]

        items = zip(contents, status_codes)
        side_effect = [
            MockRequestsResponse(content=content,
                                 status_code=status_code)
            for content, status_code in items
        ]

        patchee = 'schema_org.xml_validator.requests.get'
        self.requests_patcher = patch(patchee, side_effect=side_effect)
        self.addCleanup(self.requests_patcher.stop)
        self.requests_patcher.start()

    def test_file_like_object(self):
        """
        SCENARIO:   A file on the local file system is passed into the
        validator.  The file contains valid ISO 19115 metadata.

        SCENARIO:  no errors
        """
        validator = XMLValidator()

        content = ir.read_binary('tests.data.ieda', '600121iso.xml')
        file = io.BytesIO(content)

        validator.validate(file)

    def test_path(self):
        """
        SCENARIO:   A valid pathlib.Path object is passed into the
        validator.  The file contains valid ISO 19115 metadata.

        SCENARIO:  no errors
        """
        validator = XMLValidator()

        path = pathlib.Path('tests/data/ieda/600121iso.xml')

        validator.validate(path)

    def test_url(self):
        """
        SCENARIO:   A valid URL of a valid XML document is provided.

        SCENARIO:  no errors
        """
        content = ir.read_binary('tests.data.ieda', '600121iso.xml')
        self.setup_requests_patcher(contents=[content])

        validator = XMLValidator()

        validator.validate('http://www.acme.org/600121iso.xml')

    def test_file_like_object_but_invalid_xml(self):
        """
        SCENARIO:   A file on the local file system is passed into the
        validator.  The file contains invalid ISO 19115 metadata.

        SCENARIO:  A TypeError exception is raised.
        """
        validator = XMLValidator()

        content = ir.read_binary('tests.data.arm', 'nsanimfraod1michC2.c1.xml')
        file = io.BytesIO(content)

        with self.assertRaises(TypeError):
            validator.validate(file)
