"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os

import channels.routing
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "d1_schema_scan.settings_deploy")
django.setup()
application = channels.routing.get_default_application()
