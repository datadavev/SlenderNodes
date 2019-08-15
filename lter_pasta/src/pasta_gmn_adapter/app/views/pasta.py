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
""":mod:`views.pasta`
=====================

:Synopsis: REST call handlers for calls made by PASTA.
:Author: Roger Dahl
"""
import http.client
import re

import d1_common.const
import d1_common.date_time

import django.http

import pasta_gmn_adapter.api_types.adapter_error
import pasta_gmn_adapter.app.restrict_to_verb
import pasta_gmn_adapter.app.sql
from pasta_gmn_adapter import api_types

# ------------------------------------------------------------------------------
# PASTA system API
#
# Methods that are called automatically by PASTA
# ------------------------------------------------------------------------------


def _add_http_date_to_response_header(response, date_time):
  response['Date'] = d1_common.date_time.http_datetime_str_from_dt(date_time)


def _http_response_with_boolean_true_type():
  return django.http.HttpResponse('OK', d1_common.const.CONTENT_TYPE_TEXT)


@pasta_gmn_adapter.app.restrict_to_verb.post
def add_package_to_queue(request):
  """^adapter/new_package/?$
  """
  scope, identifier, revision = _parse_package_id(request.body.decode('utf-8'))
  _raise_if_current_revision_exists(scope, identifier, revision)
  _raise_if_later_revision_exists(scope, identifier, revision)
  pasta_gmn_adapter.app.sql.insert_population_queue_item(
    scope, identifier, revision
  )
  return _http_response_with_boolean_true_type()


def _parse_package_id(package_id):
  m = re.match(r'(.*)\.(\d+)\.(\d+)\s*$', package_id)
  if not m:
    raise pasta_gmn_adapter.api_types.adapter_error.AdapterError(
      description='Invalid package ID: {0}'.format(package_id),
      http_status_code=http.HTTPStatus.BAD_REQUEST
    )
  scope = m.group(1)
  identifier = int(m.group(2))
  revision = int(m.group(3))
  return scope, identifier, revision


def _raise_if_current_revision_exists(scope, identifier, revision):
  latest_revision = pasta_gmn_adapter.app.sql.select_latest_package_revision(
    scope, identifier
  )
  if latest_revision is not None and latest_revision == revision:
    raise pasta_gmn_adapter.api_types.adapter_error.AdapterError(
      description='Invalid package: {0}.{1}.{2}. Package already exists'
      .format(scope, identifier, revision,
              latest_revision), http_status_code=http.HTTPStatus.BAD_REQUEST
    )


def _raise_if_later_revision_exists(scope, identifier, revision):
  latest_revision = pasta_gmn_adapter.app.sql.select_latest_package_revision(
    scope, identifier
  )
  if latest_revision is not None and latest_revision > revision:
    raise pasta_gmn_adapter.api_types.adapter_error.AdapterError(
      description='Invalid package: {0}.{1}.{2}. Later revision {3} already exists'
      .format(scope, identifier, revision,
              latest_revision), http_status_code=http.HTTPStatus.BAD_REQUEST
    )
