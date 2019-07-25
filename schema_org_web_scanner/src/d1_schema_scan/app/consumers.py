import datetime
import json
import logging
import os
import subprocess
import sys

import channels.db
import channels.generic.websocket
import channels.layers
import django.conf
import redis

import d1_schema_scan.app.models
import d1_schema_scan.app.util
import d1_schema_scan.app.workers

log = logging.getLogger(__name__)


class ClientLogConsumer(channels.generic.websocket.AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        """Each WebSocket connection gets a separate instance of this class, so
        information about the connected client can be stored in attributes.
        """
        super(ClientLogConsumer, self).__init__(*args, **kwargs)
        self.redis = redis.Redis()
        self.scan_id = None
        self.scan_dict = None

    async def connect(self):
        """Handle: Client is attempting to establish a WebSocket connection.

        Join group of clients watching a single scan. Since most scans will have only
        one client, the main functionality of this is to add a known name for this scan
        as an alias for the internally generated unique name for this consumer, so that
        messages can be sent to this consumer by other consumers, by sending to the
        group name. As a nice side effect, multiple clients can open the same group and
        watch the progress.
        """
        self.scan_id = self.scope["url_route"]["kwargs"]["scan_id"]
        self.scan_dict = await self._get_scan_dict()
        log.debug(
            f'Client connecting. scan_id="{self.scan_id}" scan_url="{self.scan_dict["scan_url"]}" format_id="{self.scan_dict["format_id"]}"'
        )

        await self.channel_layer.group_add(self.scan_id, self.channel_name)

        # if not is_running(scan_id):
        await self.channel_layer.send(
            "scan",
            {
                "type": "start.scan",
                "scan_id": self.scan_id,
                "scan_url": self.scan_dict['scan_url'],
                "format_id": self.scan_dict['format_id'],
                "log_path": d1_schema_scan.app.util.get_abs_log_file_path(self.scan_id),
            },
        )

        # Accept the connection.
        await self.accept()

    async def disconnect(self, close_code):
        """Handle: Client has disconnected the WebSocket connection."""
        log.debug(f'Client disconnected. scan_id="{self.scan_id}"')
        d1_schema_scan.app.workers.status.set_stop(self.scan_id)
        await self.channel_layer.group_discard(self.scan_id, self.channel_name)

    # noinspection PyMethodOverriding
    async def receive(self, text_data):
        """Handle: Client has sent a message."""
        msg_dict = json.loads(text_data)
        log.warning(f"Client sent unhandled message: {msg_dict}")

    async def client_add_log_lines(self, msg_dict):
        """Handle: Consumer has sent new log lines to be forwarded to client"""
        log.debug(f"Consumer sent new log lines. msg_dict={msg_dict}")
        await self.send(
            text_data=json.dumps({"log_line_list": msg_dict["log_line_list"]})
        )

    async def client_scan_completed(self, msg_dict):
        """Handle: Consumer has sent notification to client that scan is completed"""
        log.debug("Consumer sent scan_completed")
        log.debug(msg_dict["exit_code"])
        d = {
            "scan_completed": True,
            "scan_end": d1_schema_scan.app.util.format_ts(
                d1_schema_scan.app.util.utc_now()
            ),
            "exit_code": d1_schema_scan.app.util.format_exit_code(
                msg_dict["exit_code"]
            ),
        }
        log.debug(d)
        await self.send(text_data=json.dumps(d))

    @channels.db.database_sync_to_async
    def _get_scan_dict(self):
        """Get the URL to scan for a given scan_id."""
        try:
            scan_model = d1_schema_scan.app.models.Scan.objects.get(scan_id=self.scan_id)
            return {
                'scan_url': scan_model.scan_url,
                'format_id': scan_model.format_id,
            }
        except d1_schema_scan.app.models.Scan.DoesNotExist:
            log.warning(f"Unknown scan_id: {self.scan_id}")


class ScannerConsumer(channels.generic.websocket.AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super(ScannerConsumer, self).__init__(*args, **kwargs)
        self.redis = redis.Redis(host="localhost", port=6379, db=0)
        self.popen_obj = None
        self.log_file = None
        self.scan_id = None
        self.scan_url = None
        self.format_id = None
        self.log_path = None
        self.max_log_lines = None

    async def start_scan(self, msg_dict):
        """Handle: Consumer requests new scan."""
        log.debug(f"New scan requested: {msg_dict}")
        self.scan_id = msg_dict["scan_id"]
        self.scan_url = msg_dict["scan_url"]
        self.format_id = msg_dict["format_id"]
        self.log_path = msg_dict["log_path"]
        self.max_log_lines = int(django.conf.settings.MAX_LOG_LINES)

        d1_schema_scan.app.workers.status.set_running(self.scan_id)

        self.log_file = open(self.log_path, "w")

        log.debug("Running scan")

        try:
            await self._run_scan()
        except Exception:
            log.exception(__file__)
        finally:
            self.log_file.close()
            self.popen_obj.communicate()
            self.popen_obj.kill()
            exit_code = self.popen_obj.wait()

        await self._set_completed(exit_code)

        d1_schema_scan.app.workers.status.set_stop(self.scan_id)
        d1_schema_scan.app.workers.status.set_completed(self.scan_id)

        await self._send_scan_completed(exit_code)

        log.debug(f'Scan exit. scan_id="{self.scan_id}"')

    async def _run_scan(self):
        arg_list = [
            django.conf.settings.PY_BIN_PATH,
            "-u",  # unbuffered
        ]
        if self.format_id:
            arg_list.extend([
                django.conf.settings.D1_VALIDATE_SCHEMA_PATH,
                self.scan_url,
                self.format_id,
            ])
        else:
            arg_list.extend([
                django.conf.settings.D1_CHECK_SITE_PATH,
                self.scan_url,
            ])

        log.info('Launching scanner subprocess: {}'.format(', '.join(arg_list)))

        self.popen_obj = subprocess.Popen(arg_list,
            bufsize=0,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        for i in range(self.max_log_lines):
            if d1_schema_scan.app.workers.status.is_stop_requested(self.scan_id):
                await self._add_log("Stopped by user.")
                return 0

            exit_code = self.popen_obj.poll()
            if exit_code is not None:
                await self._add_log(f"Worker completed with exit code: {exit_code}")
                return exit_code

            # line = "{}".format(i)
            line = self.popen_obj.stdout.readline().decode("utf-8").rstrip()
            if line is None:
                await self._add_log("Received EOF from worker")
                return 32

            await self._add_log(line)

        await self._add_log(f"Log reached {self.max_log_lines} line limit.")
        await self._add_log("Please restart with smaller scan.")

        return 32 + 1

    async def _add_log(self, log_line_str_or_list):
        """Add a log line str or list of log lines.

        If a str, log_line can be a single or multiple lines.
        """
        if isinstance(log_line_str_or_list, str):
            log_line_list = log_line_str_or_list.splitlines(keepends=False)
        else:
            log_line_list = log_line_str_or_list

        for log_line_str in log_line_list:
            await self._send_log_line(log_line_str)

    async def _send_log_line(self, log_line_str):
        log.debug(f"Sending log line to all clients in group: {log_line_str}")
        self.log_file.write(log_line_str + "\n")
        await self.channel_layer.group_send(
            self.scan_id,
            {"type": "client.add.log.lines", "log_line_list": [log_line_str]},
        )

    async def _send_scan_completed(self, exit_code):
        log.debug(
            f'Sending scan_completed to all clients in group. exit_code="{exit_code}"'
        )
        await self.channel_layer.group_send(
            self.scan_id, {"type": "client.scan_completed", "exit_code": str(exit_code)}
        )

    @channels.db.database_sync_to_async
    def _set_completed(self, exit_code):
        """Record scan as completed in DB."""
        try:
            scan_model = d1_schema_scan.app.models.Scan.objects.get(
                scan_id=self.scan_id
            )
        except d1_schema_scan.app.models.Scan.DoesNotExist:
            log.warning(f"Unknown scan_id: {self.scan_id}")
        else:
            scan_model.end_timestamp = datetime.datetime.now(datetime.timezone.utc)
            scan_model.exit_code = exit_code
            scan_model.save()


# class ScannerConsumer(channels.generic.websocket.AsyncWebsocketConsumer):
#     def __init__(self, *args, **kwargs):
#         super(ScannerConsumer, self).__init__(*args, **kwargs)
#         self.redis = redis.Redis(host="localhost", port=6379, db=0)
#         self.log_file = None
#         self.scan_id = None
#         self.scan_url = None
#         self.log_path = None
#         self.max_log_lines = None
#
#     async def start_scan(self, msg_dict):
#         """Handle: Consumer requests new scan."""
#         log.debug(f"New scan requested: {msg_dict}")
#
#         self.scan_id = msg_dict["scan_id"]
#         self.scan_url = msg_dict["scan_url"]
#         self.log_path = msg_dict["log_path"]
#         self.max_log_lines = int(django.conf.settings.MAX_LOG_LINES)
#
#         d1_schema_scan.app.workers.status.set_running(self.scan_id)
#         exit_code = 1
#         self.log_file = open(self.log_path, "w")
#
#         log.debug("Running scan")
#
#         try:
#             exit_code = await self._run_scan()
#         except Exception:
#             log.exception(__file__)
#         finally:
#             self.log_file.close()
#
#         await self._set_completed(exit_code)
#
#         d1_schema_scan.app.workers.status.set_complete(self.scan_id)
#
#         log.debug(f'Scan exit. scan_id="{self.scan_id}"')
#
#     async def _run_scan(self):
#         i = 0
#
#         while True:
#             i += 1
#             if i == self.max_log_lines:
#                 await self._add_log(f"Reached {self.max_log_lines} log line limit.")
#                 await self._add_log("Please restart with smaller scan.")
#                 return 2
#
#             if self.redis.get("stop-" + self.scan_id) is not None:
#                 await self._add_log("Stopped by user.")
#                 return 3
#
#             # if i == 100:
#             #     await self._add_log("Exit OK")
#             #     break
#
#             # line = "{}".format(i)
#             line = (
#                 f"{i} {os.getpid()} {self.scan_url} {datetime.datetime.utcnow()} "
#                 + "x" * random.randint(0, 50)
#             )
#             await self._add_log(line)
#
#             time.sleep(0.1)
#
#     async def _add_log(self, log_line_str_or_list):
#         """Add a log line str or list of log lines.
#
#         If a str, log_line can be a single or multiple lines.
#         """
#         if isinstance(log_line_str_or_list, str):
#             log_line_list = log_line_str_or_list.splitlines(keepends=False)
#         else:
#             log_line_list = log_line_str_or_list
#
#         for log_line_str in log_line_list:
#             await self._send_log_line(log_line_str)
#
#     async def _send_log_line(self, log_line_str):
#         log.debug(f"Sending log line to client: {log_line_str}")
#         self.log_file.write(log_line_str + "\n")
#         await self.channel_layer.group_send(
#             self.scan_id,
#             {"type": "client.add.log.lines", "log_line_list": [log_line_str]},
#         )
#
#     @channels.db.database_sync_to_async
#     def _set_completed(self, exit_code):
#         """Record scan as completed in DB."""
#         try:
#             scan_model = d1_schema_scan.app.models.Scan.objects.get(
#                 scan_id=self.scan_id
#             )
#         except d1_schema_scan.app.models.Scan.DoesNotExist:
#             log.warning(f"Unknown scan_id: {self.scan_id}")
#         else:
#             scan_model.end_timestamp = datetime.datetime.now(datetime.timezone.utc)
#             scan_model.exit_code = exit_code
#             scan_model.save()
