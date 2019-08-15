import logging
import os
import re

import django.core.management.base

import d1_schema_scan.app.models
import d1_schema_scan.app.util

log = logging.getLogger(__name__)

# noinspection PyAttributeOutsideInit
class Command(django.core.management.base.BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **opt):
        d1_schema_scan.app.models.Scan.objects.all().delete()

        for item in os.listdir(d1_schema_scan.app.util.get_abs_log_store_path()):
            assert re.match(r"[0-9a-f-]*$", item)
            os.unlink(
                os.path.join(d1_schema_scan.app.util.get_abs_log_store_path(), item)
            )
