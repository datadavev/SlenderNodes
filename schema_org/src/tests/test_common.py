import unittest

# 3rd party libraries
import requests_mock

# Local imports
import schema_org


class TestCommon(unittest.TestCase):

    def assertSuccessfulDebugIngest(self, cm_output, n=1):
        """
        Verify the successful ingest.  There will be messages logged at the
        DEBUG level, and one of them must be the successful ingest message.

        Parameters
        ----------
        n : int
            Number of successful ingests.
        """
        self.assertSuccessfulIngest(cm_output, n=n, level='DEBUG')

    def assertSuccessfulIngest(self, cm_output, n=1, level='INFO'):
        """
        Verify the successful ingest.  There will be messages logged at the
        specified level, and one of them must be the successful ingest message.

        Parameters
        ----------
        n : int
            Number of successful ingests.
        level : string
            Loggng level
        """
        # print('\n'.join(cm_output))

        info_msgs = [msg for msg in cm_output if msg.startswith(level)]
        self.assertTrue(len(info_msgs) > 1)

        successful_ingest = [
            msg.find(schema_org.core.SUCCESSFUL_INGEST_MESSAGE) > -1
            for msg in info_msgs
        ]
        self.assertEqual(sum(successful_ingest), n,
                         f"Did not verify {n} records successfully ingested.")

    def assertLogMessage(self, cm_output, expected_messages, level='ERROR'):
        """
        Verify we see this log message with the given level.

        Parameters
        ----------
        cm_output : list of str
            Provided by assertLogs
        expected_messages : list or str
            Look for these message in the cm_output
        level : optional, str
            Specify the log level.
        """
        if isinstance(expected_messages, str):
            # Turn the string into a list of strings.
            expected_messages = [expected_messages]

        for expected_message in expected_messages:
            count = sum(
                msg.startswith(level)
                for msg in cm_output
                if expected_message in msg
            )

            lst = [msg for msg in cm_output if msg.startswith(level)]
            msgs_at_level = '\n\n'.join(lst)

            error_message = (
                f"Did not find \"{expected_message}\" in the logs at level "
                f"{level}.\n\nHere are the messages we did find ...\n\n"
                f"{msgs_at_level}"
            )
            self.assertTrue(count >= 1, error_message)

    def assertDebugLogMessage(self, cm_output, expected_messages):
        """
        Verify we see this log message with the DEBUG level.

        Parameters
        ----------
        cm_output : list of str
            Provided by assertLogs
        expected_messages : list or str
            Look for these message in the cm_output
        """
        self.assertLogMessage(cm_output, expected_messages, level='DEBUG')

    def assertInfoLogMessage(self, cm_output, expected_messages):
        """
        Verify we see this log message with the INFO level.

        Parameters
        ----------
        cm_output : list of str
            Provided by assertLogs
        expected_messages : list or str
            Look for these message in the cm_output
        """
        self.assertLogMessage(cm_output, expected_messages, level='INFO')

    def assertWarningLogMessage(self, cm_output, expected_messages):
        """
        Verify we see this log message with the WARNING level.

        Parameters
        ----------
        cm_output : list of str
            Provided by assertLogs
        expected_messages : list or str
            Look for these message in the cm_output
        """
        self.assertLogMessage(cm_output, expected_messages, level='WARNING')

    def assertErrorLogMessage(self, cm_output, expected_messages):
        """
        Verify we see this log message with the ERROR level.

        Parameters
        ----------
        cm_output : list of str
            Provided by assertLogs
        expected_messages : list or str
            Look for these message in the cm_output
        """
        self.assertLogMessage(cm_output, expected_messages, level='ERROR')

    def assertErrorLogCallCount(self, cm_output, n=1):
        """
        Verify we see this many log messages at the ERROR level.

        Parameters
        ----------
        cm_output : list of str
            Log messages provided by assertLogs
        n : int
            How many log calls at the ERROR level to verify.
        tokens : str or list
            Verify that these strings appear in the messages.
        """
        self.assertLogLevelCallCount(cm_output, level='ERROR', n=n)

    def assertLogLevelCallCount(self, cm_output, level='ERROR', n=1):
        """
        Verify we see this many log messages with the specified level.

        Parameters
        ----------
        cm_output : list of str
            Log messages provided by assertLogs
        n : int
            How many log calls at the given level to verify.
        """
        msgs = [msg for msg in cm_output if msg.startswith(level)]
        actual_count = len(msgs)

        if actual_count > 0:
            printable = '\n'.join(msgs)
            msg = (
                f"Detected messages a log level {level} are as follows:"
                "\n\n"
                f"{printable}"
            )
        else:
            msg = ''

        self.assertEqual(actual_count, n, msg)

    def setUpRequestsMocking(self, obj, contents=None, status_codes=None,
                             headers=None, protocol='https'):
        """
        """
        if status_codes is None:
            status_codes = [200 for item in contents]

        if contents is None:
            contents = [None for item in status_codes]

        # This will work for headers in most cases.
        if headers is None:
            headers = [{'Content-Type': 'text/html'} for item in contents]

        adapter = requests_mock.Adapter()
        obj.session.mount(f'{protocol}://', adapter)

        z = zip(contents, status_codes, headers)
        response_list = [
            {
                'content': content,
                'status_code': status_code,
                'headers': headers,
            }
            for content, status_code, headers in z
        ]

        adapter.register_uri(requests_mock.ANY, requests_mock.ANY,
                             response_list=response_list)
