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
""":mod:`register_package`
==========================

:Synopsis:
  Manually add a package to the queue. For use if package registration fails.
  For instance, PASTA does not retry a failed package registration. So, if
  PASTA-GMN was down when a new package got registered in PASTA, the package
  can be registered manually with this command. Note that this will not work
  if a newer revision of the package has already been registered.

:Author:
  Roger Dahl
"""
import argparse
import http.client
import logging
import urllib.parse

import requests

import d1_common.url

import django.core.management.base
import django.db

import pasta_gmn_adapter
import pasta_gmn_adapter.app.management.commands._util as util
import pasta_gmn_adapter.settings


class Command(django.core.management.base.BaseCommand):
  def _init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def add_arguments(self, parser):
    parser.description = __doc__
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.add_argument(
      '--debug', action='store_true', help='Debug level logging'
    )
    parser.add_argument('package_id', help='E.g., "knb-lter-nin.18.2"')

  def handle(self, *args, **options):
    util.log_setup(options['debug'])
    util.exit_if_other_instance_is_running(__name__)
    logging.info('Running management command: {}'.format(__name__))
    self._register_package(options['package_id'])

  def _register_package(self, package_id):
    self._add_to_queue(package_id)

  def _add_to_queue(self, package_id):
    response = requests.post(
      d1_common.url.joinPathElements(
        pasta_gmn_adapter.settings.ADAPTER_BASE_URL, 'pasta', 'new_package'
      ),
      data=package_id,
      headers={
        "INTERNAL_CLIENT": '1',
      },
    )
    logging.info('ADD RESPONSE: {0}'.format(response.text))
