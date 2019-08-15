import datetime
import os

import django.conf


def get_abs_log_store_path():
    return os.path.join(django.conf.settings.BASE_DIR, "d1_schema_scan", "log_store")


def get_abs_log_file_path(scan_id):
    """Get the path to the log for a given scan_id."""
    return os.path.join(get_abs_log_store_path(), str(scan_id))


def format_ts(ts):
    return ts.strftime("%Y-%m-%d %H:%M:%S Z") if ts is not None else "In progress"


def format_exit_code(exit_code):
    return str(exit_code) if exit_code is not None else "In progress"


def utc_now():
    """Return current time at UTC with timezone.
    datetime.datetime.utcnow() returns a naive datetime.
    """
    return datetime.datetime.now(datetime.timezone.utc)
