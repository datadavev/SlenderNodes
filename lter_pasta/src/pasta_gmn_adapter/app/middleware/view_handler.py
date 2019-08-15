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
:mod:`view_handler`
===================

:Synopsis: Log view accesses.
:Author: Roger Dahl
"""

import logging

import django.utils.deprecation


class ViewHandler(django.utils.deprecation.MiddlewareMixin):
  def process_view(self, request, view_func, view_args, view_kwargs):
    # Log which view is about the be called.
    logging.info(
      'View: func_name({0}) method({1}) args({2}) kwargs({3})'
      .format(view_func.__name__, request.method, view_args, view_kwargs)
    )
    # Returning None continues regular handling.
    return None
