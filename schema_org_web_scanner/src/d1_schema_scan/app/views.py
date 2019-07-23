import logging
import urllib.parse

import django.contrib.staticfiles.templatetags.staticfiles
import django.http
import django.shortcuts
import django.utils.safestring

import d1_schema_scan.app.consumers
import d1_schema_scan.app.models
import d1_schema_scan.app.util
import d1_schema_scan.app.workers

log = logging.getLogger(__name__)


def get_static_path(rel_path):
    return django.contrib.staticfiles.templatetags.staticfiles.static(rel_path)


def index(request):
    return django.shortcuts.render(request, "index.xhtml", {}, content_type="text/html")


def new(request, scan_url):
    scan_model = d1_schema_scan.app.models.Scan.objects.create(
        scan_url=urllib.parse.unquote(scan_url)
    )
    scan_model.save()
    return django.shortcuts.redirect(scan, scan_model.scan_id)


def scan(request, scan_id):
    try:
        scan_model = d1_schema_scan.app.models.Scan.objects.get(scan_id=scan_id)
    except d1_schema_scan.app.models.Scan.DoesNotExist:
        return django.shortcuts.redirect(index)

    if scan_model.exit_code is not None or d1_schema_scan.app.workers.status.is_stop_requested(scan_id):
        return django.shortcuts.redirect(view, scan_id)

    return django.shortcuts.render(
        request, "scan.xhtml", _get_result_dict(scan_model), content_type="text/html"
    )


def view(request, scan_id):
    d1_schema_scan.app.workers.status.wait_for_complete(scan_id)

    try:
        scan_model = d1_schema_scan.app.models.Scan.objects.get(scan_id=scan_id)
    except d1_schema_scan.app.models.Scan.DoesNotExist:
        return django.shortcuts.redirect(index)

    # if d1_schema_scan.app.workers.status.is_running(scan_id):
    #     return django.shortcuts.redirect(view, scan_id)

    log_path = d1_schema_scan.app.util.get_abs_log_file_path(scan_model.scan_id)

    try:
        with open(log_path, "r") as f:
            log_str = f.read()
            log.error(log_str)
    except IOError:
        log_str = "Unable to open log"
        log.error(f"Missing log file: {log_path}")
    return django.shortcuts.render(
        request,
        "view.xhtml",
        {
            **{"scan_log": log_str.splitlines(keepends=False)},
            **_get_result_dict(scan_model),
        },
        content_type="text/html",
    )


def _get_result_dict(scan_model):
    return {
        "scan_id": str(scan_model.scan_id),
        "scan_url_esc": encode_path_element(scan_model.scan_url),
        "scan_url_unesc": scan_model.scan_url,
        "scan_start": d1_schema_scan.app.util.format_ts(scan_model.start_timestamp),
        "scan_end": d1_schema_scan.app.util.format_ts(scan_model.end_timestamp),
        "exit_code": d1_schema_scan.app.util.format_exit_code(scan_model.exit_code),
    }


def encode_path_element(element):
    """Encode a URL path element according to RFC3986."""
    return urllib.parse.quote(
        (
            element.encode("utf-8")
            if isinstance(element, str)
            else str(element)
            if isinstance(element, int)
            else element
        ),
        safe=":@$!()',~*&=",
    )


def decode_path_element(element):
    """Decode a URL path element according to RFC3986."""
    return urllib.parse.unquote(element)
