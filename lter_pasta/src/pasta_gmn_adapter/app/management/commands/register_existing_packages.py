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
""":mod:`register_existing_packages`
====================================

:Synopsis:
  Populate the queue with packages that already exist on PASTA. For use when
  initially deploying PASTA-GMN.

:Author:
  Roger Dahl
"""

import argparse
import http.client
import logging
import sys
import urllib.parse

import django.core.management.base
import django.db

import pasta_gmn_adapter
import pasta_gmn_adapter.app.data_package_manager_client
# noinspection PyProtectedMember
import pasta_gmn_adapter.app.management.commands._util as util
import pasta_gmn_adapter.app.sql

debug_filter = (
  ('knb-lter-mcr', 5008),
  ('knb-lter-mcr', 32),
  ('knb-lter-luq', 107),
  ('knb-lter-knz', 205),
  ('knb-lter-knz', 205),
  ('knb-lter-cap', 514),
  ('knb-lter-cap', 514),
  ('knb-lter-sev', 190),
  ('knb-lter-knz', 33),
  ('knb-lter-knz', 9),
  ('knb-lter-kbs', 23),
  ('knb-lter-hfr', 4),
  ('knb-lter-arc', 10134),
)


class Command(django.core.management.base.BaseCommand):
  def _init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

  def add_arguments(self, parser):
    parser.description = __doc__
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.add_argument(
      '--debug', action='store_true', help='Debug level logging'
    )

  def handle(self, *args, **options):
    util.log_setup(options['debug'])
    util.exit_if_other_instance_is_running(__name__)
    logging.info('Running management command: {}'.format(__name__))
    self.register_existing_packages()

  def register_existing_packages(self):
    self._clear_database()
    self._register_packages()

  def _register_packages(self):
    c = pasta_gmn_adapter.app.data_package_manager_client.DataPackageManagerClient()
    for scope in c.list_data_package_scopes():
      ####################################################################################
      # for now, ignore ecotrends because all the packages are private.
      #if 'ecotrends' in scope:
      #  logging.info('Skipped ecotrends')
      #  continue
      for identifier in c.list_data_package_identifiers(scope):
        ##################################################################################
        # For debugging, filter all but packages that are being debugged.
        #if (scope, identifier) not in debug_filter:
        #  logging.info('Skipped {0} {1}'.format(scope, identifier))
        #  continue
        for revision in c.list_data_package_revisions(scope, identifier):
          package_id = '{0}.{1}.{2}'.format(scope, identifier, revision)
          self._add_to_queue(package_id)

  def _add_to_queue(self, package_id):
    o = urllib.parse.urlparse(pasta_gmn_adapter.settings.ADAPTER_BASE_URL)
    c = http.client.HTTPConnection(o.netloc)
    headers = {"INTERNAL_CLIENT": '1'}
    c.request('POST', o.path + '/pasta/new_package', package_id, headers)
    response = c.getresponse()
    logging.info('ADD RESPONSE: {0}'.format(response.text))

  def _clear_database(self):
    pasta_gmn_adapter.app.sql.clear_database()
