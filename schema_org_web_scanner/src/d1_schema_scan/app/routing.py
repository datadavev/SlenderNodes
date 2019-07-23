# scan/routing.py
import django.conf.urls

import d1_schema_scan.app.consumers

websocket_urlpatterns = [
    django.conf.urls.url(
        r"^ws/(?P<scan_id>.+)/$", d1_schema_scan.app.consumers.ClientLogConsumer
    )
]
