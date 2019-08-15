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
:mod:`exception_handler`
========================

:Synopsis:
  Catch, log and serialize any exceptions that are raised when processing a
  request.

  When running in Django production mode (settings.DEBUG = False), all
  exceptions are returned to the client as AdapterErrors serialized to XML.
  adapterErrors are thrown by any code in the adapter itself when an error is
  detected. When an AdapterError is caught here, it is serialized directly. When
  processing a request, Python, the standard library and 3rd party libraries can
  also throw exceptions. These are caught here, wrapped in an AdapterError and
  then serialized.

  When running in Django debug mode (settings.DEBUG = True), all exceptions are
  returned as Django HTML exception pages.

:Author: Roger Dahl
"""

import http.client
import logging
import os
import sys

import d1_common.const
import d1_common.types.exceptions

import django.utils.deprecation
from django.http import HttpResponse

import pasta_gmn_adapter
import pasta_gmn_adapter.api_types.adapter_error
from pasta_gmn_adapter import api_types


class ExceptionHandler(django.utils.deprecation.MiddlewareMixin):
  def process_exception(self, request, exception):
    logging.exception('Exception:')

    if isinstance(exception,
                  pasta_gmn_adapter.api_types.adapter_error.AdapterError):
      return self.serialize_adapter_exception(exception)
    else:
      return self.handle_unknown_exception()

  def serialize_adapter_exception(self, exception):
    exception_serialized = exception.serialize()
    return HttpResponse(
      exception_serialized, status=exception.http_status_code,
      content_type=d1_common.const.CONTENT_TYPE_XML
    )

  def handle_unknown_exception(self):
    if pasta_gmn_adapter.settings.DEBUG:
      return self.django_html_exception_page()
    else:
      return self.wrap_internal_exception_in_adapter_exception()

  def django_html_exception_page(self):
    # Returning None from the exception handler causes Django to generate
    # an HTML exception page.
    return None

  def wrap_internal_exception_in_adapter_exception(self):
    return pasta_gmn_adapter.api_types.adapter_error.AdapterError(
      description=self.traceback_to_text(),
      http_status_code=http.HTTPStatus.INTERNAL_SERVER_ERROR
    )

  def traceback_to_text(self):
    return '\n'.join(self._traceback_to_trace_info())

  def _traceback_to_trace_info(self):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    trace_info_list = []
    while exc_traceback:
      co = exc_traceback.tb_frame.f_code
      trace_info_list.append(
        '{}({})'.format(
          os.path.basename(co.co_filename),
          exc_traceback.tb_lineno,
        )
      )
      exc_traceback = exc_traceback.tb_next
    if not isinstance(exc_value, d1_common.types.exceptions.DataONEException):
      trace_info_list.append('Type: {}'.format(exc_type))
      trace_info_list.append('Value: {}'.format(exc_value))
    return trace_info_list
