import os
import sys

import d1_common.util

import django.core.wsgi

# Adding "." to the sys path here allows the folder that this file is in to be
# used as the root of import statements.
#sys.path.append(_here('.'))
#sys.path.append(_here('..'))

sys.path.append(d1_common.util.abs_path('./api_types/generated'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'pasta_gmn_adapter.settings'

application = django.core.wsgi.get_wsgi_application()
