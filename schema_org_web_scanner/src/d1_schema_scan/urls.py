import django.conf.urls
import django.contrib
import django.contrib.admin
import django.urls

import d1_schema_scan.app.views

urlpatterns = [
    django.urls.path("admin/", django.contrib.admin.site.urls),
    django.conf.urls.url(r"^$", d1_schema_scan.app.views.index, name="index"),
    django.conf.urls.url(r"^sitemap/$", d1_schema_scan.app.views.sitemap, name="sitemap"),
    django.conf.urls.url(r"^xmlschema/$", d1_schema_scan.app.views.xmlschema, name="xmlschema"),
    django.conf.urls.url(
        r"^new/xmlschema/(?P<scan_url>.+)/(?P<format_id>.+)/$", d1_schema_scan.app.views.new_xmlschema, name="new-xmlschema"
    ),
    django.conf.urls.url(
        r"^new/sitemap/(?P<scan_url>.+)/$", d1_schema_scan.app.views.new_sitemap, name="new-sitemap"
    ),
    django.conf.urls.url(
        r"^scan/(?P<scan_id>.+)/$", d1_schema_scan.app.views.scan, name="scan"
    ),
    django.conf.urls.url(
        r"^view/(?P<scan_id>.+)/$", d1_schema_scan.app.views.view, name="view"
    ),
]
