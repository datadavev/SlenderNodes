#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
:mod:`urls`
===========

:Synopsis: URL to function mapping.
:Author: Roger Dahl
"""

import django.conf.urls as urls

import pasta_gmn_adapter.app.views.admin
import pasta_gmn_adapter.app.views.pasta

urlpatterns = [
  urls.url(
    r'^pasta/new_package/?$',
    pasta_gmn_adapter.app.views.pasta.add_package_to_queue
  ),
  # Admin
  urls.url(r'^admin/$', pasta_gmn_adapter.app.views.admin.admin),
  # Statistics.
  urls.url(
    r'^admin/statistics/?$', pasta_gmn_adapter.app.views.admin.get_statistics
  ),
  urls.url(
    r'^admin/statistics\.xsl$',
    pasta_gmn_adapter.app.views.admin.get_statistics_xsl
  ),
  # Population Queue.
  urls.url(
    r'^admin/population_queue/?$',
    pasta_gmn_adapter.app.views.admin.get_population_queue
  ),
  urls.url(
    r'^admin/population_queue\.xsl$',
    pasta_gmn_adapter.app.views.admin.get_population_queue_xsl
  ),
  # Status.
  urls.url(
    r'^admin/status/(.*)$', pasta_gmn_adapter.app.views.admin.get_status
  ),
  urls.url(
    r'^admin/status\.xsl$', pasta_gmn_adapter.app.views.admin.get_status_xsl
  ),
]
