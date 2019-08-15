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
""":mod:`views.admin`
=====================

:Synopsis:
  Administrator functionality.
:Author: Roger Dahl
"""
import d1_common.const

import django.shortcuts

import pasta_gmn_adapter
import pasta_gmn_adapter.app.restrict_to_verb
import pasta_gmn_adapter.app.sql

# ------------------------------------------------------------------------------
# Admin portal.
# ------------------------------------------------------------------------------


@pasta_gmn_adapter.app.restrict_to_verb.get
def admin(request):
  if pasta_gmn_adapter.settings.GMN_ADAPTER_DEBUG:
    if 'clear_database' in request.GET:
      pasta_gmn_adapter.app.sql.clear_database()
  return django.shortcuts.render_to_response(
    'admin.html', {'debug': pasta_gmn_adapter.settings.GMN_ADAPTER_DEBUG},
    content_type=d1_common.const.CONTENT_TYPE_XHTML
  )


# Statistics


@pasta_gmn_adapter.app.restrict_to_verb.get
def get_statistics(_request):
  p = pasta_gmn_adapter.app.sql.select_statistics()
  return django.shortcuts.render_to_response(
    'statistics.xml', {'statistics': p},
    content_type=d1_common.const.CONTENT_TYPE_XML
  )


@pasta_gmn_adapter.app.restrict_to_verb.get
def get_statistics_xsl(_request):
  return django.shortcuts.render_to_response(
    'statistics.xsl', content_type=d1_common.const.CONTENT_TYPE_XML
  )


# Population Queue


@pasta_gmn_adapter.app.restrict_to_verb.get
def get_population_queue(request):
  if 'excludecompleted' in request.GET:
    p = pasta_gmn_adapter.app.sql.select_population_queue_with_latest_status_uncompleted()
  else:
    p = pasta_gmn_adapter.app.sql.select_population_queue_with_latest_status()
  #return HttpResponse(p)
  return django.shortcuts.render_to_response(
    'population_queue.xml', {'population_queue': p},
    content_type=d1_common.const.CONTENT_TYPE_XML
  )


@pasta_gmn_adapter.app.restrict_to_verb.get
def get_population_queue_xsl(_request):
  return django.shortcuts.render_to_response(
    'population_queue.xsl', content_type=d1_common.const.CONTENT_TYPE_XML
  )


# Status


@pasta_gmn_adapter.app.restrict_to_verb.get
def get_status(_request, population_queue_id):
  p = pasta_gmn_adapter.app.sql.select_status(population_queue_id)
  return django.shortcuts.render_to_response(
    'status.xml', {'status': p}, content_type=d1_common.const.CONTENT_TYPE_XML
  )


@pasta_gmn_adapter.app.restrict_to_verb.get
def get_status_xsl(_request):
  return django.shortcuts.render_to_response(
    'status.xsl', content_type=d1_common.const.CONTENT_TYPE_XML
  )
