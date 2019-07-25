import uuid

import django.contrib.admin
import django.db.models


class Scan(django.db.models.Model):
    scan_id = django.db.models.UUIDField(primary_key=True, default=uuid.uuid4)
    scan_url = django.db.models.URLField(max_length=300)
    format_id = django.db.models.URLField(max_length=30, null=True)
    start_timestamp = django.db.models.DateTimeField(auto_now=True)
    end_timestamp = django.db.models.DateTimeField(null=True)
    exit_code = django.db.models.IntegerField(null=True)


django.contrib.admin.site.register(Scan)
