import logging
import time

import django.conf
import redis

log = logging.getLogger(__name__)


class WorkerStatus:
    def __init__(self):
        self.redis = redis.Redis(
            host=django.conf.settings.REDIS_HOST,
            port=django.conf.settings.REDIS_PORT,
            db=django.conf.settings.REDIS_DB,
        )

    def set_running(self, scan_id):
        self.redis.set(self._running_key(scan_id), 1)

    def set_stop(self, scan_id):
        self.redis.set(self._stop_key(scan_id), 1)

    def set_completed(self, scan_id):
        self.redis.set(self._completed_key(scan_id), 1)

    def is_stop_requested(self, scan_id):
        return self._has_stop(scan_id)

    def is_running(self, scan_id):
        return self._flags(scan_id) in ((True, False, False), (True, True, False))

    def is_completed(self, scan_id):
        return self._flags(scan_id) in ((False, False, False), (True, True, True))

    def wait_for_complete(self, scan_id):
        while not self.is_completed(scan_id):
            time.sleep(0.1)

    def _running_key(self, scan_id):
        return f"running-{scan_id}"

    def _stop_key(self, scan_id):
        return f"stop-{scan_id}"

    def _completed_key(self, scan_id):
        return f"completed-{scan_id}"

    def _has_running(self, scan_id):
        return bool(self.redis.exists(self._running_key(scan_id)))

    def _has_stop(self, scan_id):
        return bool(self.redis.exists(self._stop_key(scan_id)))

    def _has_completed(self, scan_id):
        return bool(self.redis.exists(self._completed_key(scan_id)))

    def _flags(self, scan_id):
        flags_tup = tuple(
            bool(v)
            for v in self.redis.mget(
                self._running_key(scan_id),
                self._stop_key(scan_id),
                self._completed_key(scan_id),
            )
        )
        log.debug(f"Worker flags: {scan_id}: {flags_tup}")
        return flags_tup


status = WorkerStatus()
