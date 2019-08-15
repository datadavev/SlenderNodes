import os

import django.core.wsgi

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "d1_schema_scan.settings_deploy")

application = django.core.wsgi.get_wsgi_application()
