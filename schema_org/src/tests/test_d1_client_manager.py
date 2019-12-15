# Standard library imports
import datetime as dt
import hashlib
try:
    import importlib.resources as ir
except ImportError:  # pragma:  nocover
    import importlib_resources as ir
import unittest
from unittest.mock import patch, Mock

# 3rd party library imports
import d1_common.types.dataoneTypes_v2_0 as v2
import d1_common.types.exceptions
import d1_common.checksum

# local imports
from schema_org.d1_client_manager import D1ClientManager


@patch('schema_org.d1_client_manager.d1_client.mnclient_2_0.MemberNodeClient_2_0')  # noqa: E501
class TestD1ClientManager(unittest.TestCase):

    def setUp(self):
        self.gmn_base_url = 'https://localhost/gm'
        self.auth_cert = None
        self.auth_cert_key = None
        self.mock_logger = Mock()

    def _generate_system_metadata(self, scimeta_bytes, sid, pid, record_date):

        sys_meta = v2.systemMetadata()
        sys_meta.seriesId = sid
        sys_meta.formatId = 'http://www.isotc211.org/2005/gmd-ieda'
        sys_meta.size = len(scimeta_bytes)

        digest = hashlib.md5(scimeta_bytes).hexdigest()
        sys_meta.checksum = v2.checksum(digest)
        sys_meta.checksum.algorithm = 'MD5'

        sys_meta.identifier = sys_meta.checksum.value()
        sys_meta.dateUploaded = record_date
        sys_meta.dateSysMetadataModified = dt.datetime.now()

        sys_meta.identifier = pid
        sys_meta.dateUploaded = d1_common.date_time.utc_now()
        sys_meta.dateSysMetadataModified = dt.datetime.now()
        sys_meta.rightsHolder = 'urn:node:IEDA'
        sys_meta.submitter = 'urn:node:IEDA'
        sys_meta.authoritativeMemberNode = 'urn:node:mnTestIEDA'
        sys_meta.originMemberNode = 'urn:node:IEDA'
        sys_meta.accessPolicy = v2.AccessPolicy()

        return sys_meta

    def test_get_last_harvest_time_with_objects_in_the_system(self,
                                                              mock_client):
        """
        SCENARIO:  There are valid objects in the system and we ask for the
        last harvest time.

        EXPECTED RESULT:  The last harvest time is earlier than logically
        possible.
        """
        # We need to dive pretty deep to mock everything out here.
        the_time = dt.datetime(1900, 1, 1, 0, 0, 0)
        mock_objectInfo = Mock()
        mock_objectInfo.return_value.dateSysMetadataModified = the_time

        config = {
            # So there's at least one object.
            'return_value.listObjects.return_value.total': 1,
            # That first object has a specific date attached to it.
            'return_value.listObjects.return_value.objectInfo': [mock_objectInfo()],  # noqa: E501
        }
        mock_client.configure_mock(**config)

        client_mgr = D1ClientManager(self.gmn_base_url,
                                     self.auth_cert,
                                     self.auth_cert_key,
                                     self.mock_logger)

        time = client_mgr.get_last_harvest_time()

        self.assertEqual(time, '1900-01-01T00:00:00Z')

    def test_get_last_harvest_time_shows_no_objects_are_there(self,
                                                              mock_client):
        """
        SCENARIO:  There are no objects in the system and we ask for the last
        harvest time.

        EXPECTED RESULT:  The last harvest time is earlier than logically
        possible.
        """
        mock_client.return_value.listObjects.return_value.total = 0

        client_mgr = D1ClientManager(self.gmn_base_url,
                                     self.auth_cert,
                                     self.auth_cert_key,
                                     self.mock_logger)
        time = client_mgr.get_last_harvest_time()

        self.assertEqual(time, '1900-01-01T00:00:00Z')

    @patch('schema_org.d1_client_manager.sys.exit')
    def test_get_last_harvest_time_fails(self, mock_sys_exit, mock_client):
        """
        SCENARIO:  We fail to get the last harvest time.

        EXPECTED RESULT:  There are two calls to the logger at the error level.
        The system attempts to exit.
        """
        # This causes the failure.
        mock_client.return_value.listObjects.side_effect = RuntimeError('something bad')  # noqa: E501

        client_mgr = D1ClientManager(self.gmn_base_url,
                                     self.auth_cert, self.auth_cert_key,
                                     self.mock_logger)
        client_mgr.get_last_harvest_time()

        self.assertEqual(mock_sys_exit.call_count, 1)
        self.assertEqual(self.mock_logger.error.call_count, 2)

    def test_positive_check_if_identifier_exists(self, mock_client):
        """
        SCENARIO:  An identifier already exists in the system.

        EXPECTED RESULT:  A dictionary of expected information.
        """
        expected_date = '1900-01-01'
        expected_version_id = 'v2'
        config = {
            'return_value.getSystemMetadata.return_value.dateUploaded': expected_date,  # noqa: E501
            'return_value.getSystemMetadata.return_value.identifier.value.return_value': expected_version_id,  # noqa: E501
        }
        mock_client.configure_mock(**config)

        # mock_client.return_value.getSystemMetadata.return_value = expected

        client_mgr = D1ClientManager(self.gmn_base_url,
                                     self.auth_cert, self.auth_cert_key,
                                     None)
        actual = client_mgr.check_if_identifier_exists('thing')

        expected = {
            'outcome': 'yes',
            'record_date': expected_date,
            'current_version_id': expected_version_id,
        }
        self.assertEqual(actual, expected)

    def test_negative_check_if_identifier_exists(self, mock_client):
        """
        SCENARIO:  An identifier does not exists in the system.

        EXPECTED RESULT:  A dictionary of expected information.
        """
        mock_client.return_value.getSystemMetadata.side_effect = d1_common.types.exceptions.NotFound('bad')  # noqa: E501

        client_mgr = D1ClientManager(self.gmn_base_url,
                                     self.auth_cert, self.auth_cert_key,
                                     None)
        actual = client_mgr.check_if_identifier_exists('thing')

        expected = {
            'outcome': 'no',
        }
        self.assertEqual(actual, expected)

    def test_unknown_exception_check_if_identifier_exists(self, mock_client):
        """
        SCENARIO:  An unexpected exception happened when we checked for the
        given identifier.

        EXPECTED RESULT:  A dictionary of expected information and the
        exception is logged.
        """
        mock_client.return_value.getSystemMetadata.side_effect = RuntimeError('bad')  # noqa: E501
        mock_logger = Mock()

        client_mgr = D1ClientManager(self.gmn_base_url,
                                     self.auth_cert, self.auth_cert_key,
                                     mock_logger)
        actual = client_mgr.check_if_identifier_exists('thing')

        expected = {
            'outcome': 'failed',
        }
        self.assertEqual(actual, expected)
        self.assertEqual(mock_logger.error.call_count, 2)

    def test_load_science_metadata(self, mock_client):
        """
        SCENARIO:  A new science metadata record is successfully loaded.

        EXPECTED RESULT:  True
        """
        sci_metadata_bytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        sid = 'i_am_a_sid'
        record_date = dt.datetime.now().isoformat()
        pid = '1'

        client_mgr = D1ClientManager(self.gmn_base_url,
                                     self.auth_cert, self.auth_cert_key,
                                     self.mock_logger)

        system_metadata = self._generate_system_metadata(sci_metadata_bytes,
                                                         sid,
                                                         pid,
                                                         record_date)
        actual = client_mgr.load_science_metadata(
            sci_metadata_bytes=sci_metadata_bytes,
            native_identifier_sid=sid,
            record_date=record_date,
            system_metadata=system_metadata
        )

        self.assertTrue(actual)

    def test_load_science_metadata__create_errors_out(self, mock_client):
        """
        SCENARIO:  A new science metadata record is not successfully loaded
        because the create routine errors out for some reason.

        EXPECTED RESULT:  False, and the failure is logged at the error level.
        """
        mock_client.return_value.create.side_effect = RuntimeError('something bad happened')  # noqa: E501

        sci_metadata_bytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        sid = 'i_am_a_sid'
        record_date = dt.datetime.now().isoformat()
        pid = '1'

        client_mgr = D1ClientManager(
            self.gmn_base_url,
            self.auth_cert, self.auth_cert_key,
            self.mock_logger
        )

        system_metadata = self._generate_system_metadata(sci_metadata_bytes,
                                                         sid,
                                                         pid,
                                                         record_date)
        actual = client_mgr.load_science_metadata(
            sci_metadata_bytes=sci_metadata_bytes,
            native_identifier_sid=sid,
            record_date=record_date,
            system_metadata=system_metadata
        )

        self.assertFalse(actual)
        self.assertEqual(self.mock_logger.error.call_count, 2)

    def test_update_science_metadata(self, mock_client):
        """
        SCENARIO:  A new science metadata record is successfully loaded.

        EXPECTED RESULT:  True
        """
        sci_metadata_bytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        sid = 'i_am_a_sid'
        record_date = dt.datetime.now().isoformat()
        old_version_pid = 'b645a195302ca652ec39f1bf3b908dbf'

        client_mgr = D1ClientManager(
            self.gmn_base_url, self.auth_cert, self.auth_cert_key, None
        )
        system_metadata = self._generate_system_metadata(sci_metadata_bytes,
                                                         sid,
                                                         old_version_pid,
                                                         record_date)
        actual = client_mgr.update_science_metadata(
            sci_metadata_bytes=sci_metadata_bytes,
            native_identifier_sid=sid,
            record_date=record_date,
            old_version_pid=old_version_pid,
            system_metadata=system_metadata
        )
        self.assertTrue(actual)

    def test_update_science_metadata_fails(self, mock_client):
        """
        SCENARIO:  A new science metadata record is not successfully updated
        because the update routine errors out for some reason.

        EXPECTED RESULT:  False, and the failure is logged at the error level.
        """
        mock_client.return_value.update.side_effect = RuntimeError('something bad happened')  # noqa: E501

        sci_metadata_bytes = ir.read_binary('tests.data.ieda', '600121iso.xml')
        sid = 'i_am_a_sid'
        record_date = dt.datetime.now().isoformat()
        old_version_pid = 'b645a195302ca652ec39f1bf3b908dbf'

        mock_logger = Mock()

        client_mgr = D1ClientManager(
            self.gmn_base_url,
            self.auth_cert, self.auth_cert_key,
            mock_logger
        )
        system_metadata = self._generate_system_metadata(sci_metadata_bytes,
                                                         sid,
                                                         old_version_pid,
                                                         record_date)
        actual = client_mgr.update_science_metadata(
            sci_metadata_bytes=sci_metadata_bytes,
            native_identifier_sid=sid,
            record_date=record_date,
            old_version_pid=old_version_pid,
            system_metadata=system_metadata
        )
        self.assertFalse(actual)
        self.assertEqual(mock_logger.error.call_count, 2)

    def test_archive_science_metadata(self, mock_client):
        """
        SCENARIO:  A science metadata record is successfully archived.

        EXPECTED RESULT:  True
        """
        current_version_pid = 'b645a195302ca652ec39f1bf3b908dbf'

        client_mgr = D1ClientManager(
            self.gmn_base_url,
            self.auth_cert, self.auth_cert_key,
            None
        )
        actual = client_mgr.archive_science_metadata(current_version_pid)
        self.assertTrue(actual)

    def test_archive_science_metadata_fails(self, mock_client):
        """
        SCENARIO:  A science metadata record is not successfully archived
        because the archive routine errors out for some reason.

        EXPECTED RESULT:  False, and the failure is logged at the error level.
        """
        mock_client.return_value.archive.side_effect = RuntimeError('something bad happened')  # noqa: E501

        current_version_pid = 'b645a195302ca652ec39f1bf3b908dbf'

        client_mgr = D1ClientManager(
            self.gmn_base_url,
            self.auth_cert, self.auth_cert_key,
            self.mock_logger
        )
        actual = client_mgr.archive_science_metadata(current_version_pid)

        self.assertFalse(actual)
        self.assertEqual(self.mock_logger.error.call_count, 2)

    def test_verify_tls(self, mock_client):
        """
        SCENARIO:  Paths to a client side cert and key are provided.

        EXPECTED RESULT:  No error on initialization.
        """
        D1ClientManager(
            self.gmn_base_url,
            '/path/to/cert', '/path/to/key',
            None,
        )
        self.assertTrue(True)
