import logging
import urllib.parse

# import django.contrib.staticfiles.templatetags.staticfiles
import django.http
import django.shortcuts
import django.utils.safestring

import d1_schema_scan.app.consumers
import d1_schema_scan.app.models
import d1_schema_scan.app.util
import d1_schema_scan.app.workers
import pathlib

log = logging.getLogger(__name__)


def dbg(request):
    import pprint

    log.info(pprint.pformat(request.META))


def get_static_path(*path_segment_list):
    # return django.contrib.staticfiles.templatetags.staticfiles.static(rel_path)
    path_segment_list = [
        pathlib.Path(s).as_posix().lstrip('/') for s in path_segment_list
    ]
    # if url_path.is_absolute():
    #     url_path = url_path.relative_to('/')
    return pathlib.Path(django.conf.settings.STATIC_ROOT, *path_segment_list)


def get_abs_static_url(request, rel_path):
    import django.contrib.staticfiles.storage

    return request.build_absolute_uri(
        django.contrib.staticfiles.storage.staticfiles_storage.url(rel_path)
    )


def index(request):
    return django.shortcuts.render(
        request, "index.xhtml", _gen_context_dict(request), content_type="text/html"
    )


def sitemap(request):
    return django.shortcuts.render(
        request, "sitemap.xhtml", _gen_context_dict(request), content_type="text/html"
    )


def xmlschema(request):
    return django.shortcuts.render(
        request, "xmlschema.xhtml", _gen_context_dict(request), content_type="text/html"
    )


def new_sitemap(request, scan_url):
    scan_model = d1_schema_scan.app.models.Scan.objects.create(
        scan_url=urllib.parse.unquote(scan_url)
    )
    scan_model.save()
    return django.shortcuts.redirect(scan, scan_model.scan_id)


def new_xmlschema(request, scan_url, format_id):
    scan_model = d1_schema_scan.app.models.Scan.objects.create(
        scan_url=urllib.parse.unquote(scan_url),
        format_id=urllib.parse.unquote(format_id),
    )
    scan_model.save()
    return django.shortcuts.redirect(scan, scan_model.scan_id)


def scan(request, scan_id):
    try:
        scan_model = d1_schema_scan.app.models.Scan.objects.get(scan_id=scan_id)
    except d1_schema_scan.app.models.Scan.DoesNotExist:
        return django.shortcuts.redirect(index)

    if (
        scan_model.exit_code is not None
        or d1_schema_scan.app.workers.status.is_stop_requested(scan_id)
    ):
        return django.shortcuts.redirect(view, scan_id)

    return django.shortcuts.render(
        request,
        "scan.xhtml",
        _gen_context_dict(request, scan_model=scan_model),
        content_type="text/html",
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
        _gen_context_dict(request, log_str, scan_model),
        content_type="text/html",
    )


def _gen_context_dict(request, log_str=None, scan_model=None):
    arg_dict = {
        "samples_base_url": encode_path_element(get_abs_static_url(request, "samples"))
    }
    if log_str:
        arg_dict["scan_log"] = log_str.splitlines(keepends=False)
    if scan_model:
        arg_dict.update(_get_result_dict(scan_model))
    return arg_dict


def _get_result_dict(scan_model):
    return {
        "scan_id": str(scan_model.scan_id),
        "scan_url_esc": encode_path_element(scan_model.scan_url),
        "scan_url_unesc": scan_model.scan_url,
        "format_id_esc": encode_path_element(scan_model.format_id)
        if scan_model.format_id
        else None,
        "format_id_unesc": scan_model.format_id if scan_model.format_id else None,
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
