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
""":mod:`tests`
===============

:Synopsis:
  Unit tests for the adapter.

  May have to give the pasta_gmn_adapter user createdb permission:

  $ sudo -u postgres psql template1
  template1=# alter user pasta_gmn_adapter createdb

  Run the tests with: ./manage.py test

:Author:
  Roger Dahl
"""

import pytest

import d1_common.types.dataoneTypes

import django.db
import django.db.transaction
import django.test
import django.utils

import pasta_gmn_adapter
import pasta_gmn_adapter.app.data_package_manager_client
import pasta_gmn_adapter.app.sql
from pasta_gmn_adapter import api_types

# App.

TEST_EML_ACCESS_XML = """<access:access xmlns:access="eml://ecoinformatics.org/access-2.1.0" authSystem="https://pasta.lternet.edu/authentication" order="allowFirst" system="https://pasta.lternet.edu">
  <allow>
    <principal>uid=dcosta,o=LTER,dc=ecoinformatics,dc=org</principal>
    <permission>changePermission</permission>
  </allow>
  <allow>
    <principal>uid=PIE,o=lter,dc=ecoinformatics,dc=org</principal>
    <permission>changePermission</permission>
  </allow>
  <allow>
    <principal>public</principal>
    <permission>read</permission>
  </allow>
</access:access>
"""


class TestSQL(django.test.TestCase):
  # Tried using setUpClass() to get Django to retain the table contents between
  # tests, but couldn't get it to work. Also tried forcing transactions to be
  # committed.
  @classmethod
  def setUpClass(cls):
    pass

  @classmethod
  def tearDownClass(cls):
    pass

  def setUp(self):
    # Create a blank copy of the database. This is equivalent to the fixtures
    # Django would normally create from the models in models.py.
    create_sql = open('pasta_gmn_adapter.sql').read()
    cursor = django.db.connection.cursor()
    cursor.execute(create_sql)

    # django.db.transaction.commit()

  def tearDown(self):
    pass

  def _populate_with_test_objects(self):
    pasta_gmn_adapter.app.sql.insert_population_queue_item(
      'test_package', 111, 222
    )
    pasta_gmn_adapter.app.sql.insert_population_queue_item(
      'test_package_2', 333, 444
    )
    queue_id = pasta_gmn_adapter.app.sql.insert_population_queue_item(
      'test_package_2', 333, 445
    )
    pasta_gmn_adapter.app.sql.insert_population_queue_item(
      'test_package_3', 555, 666
    )

    status_id = pasta_gmn_adapter.app.sql.insert_process_status(
      queue_id, 'completed'
    )
    #
    # cursor = django.db.connection.cursor()
    #
    # cursor.execute(
    # """
    # update queue_id
    # insert into adapter_population_queue_package_scope (package_scope)
    # select %s where not exists (
    #   select id from adapter_population_queue_package_scope where package_scope = %s
    # );
    # """,
    # [scope, scope]

  # )

  def test_100_insert_population_queue_item(self):
    self._populate_with_test_objects()
    q = pasta_gmn_adapter.app.sql.select_population_queue_all()
    self.assertEqual(len(q), 4)
    self.assertEqual(q[0]['package_identifier'], 111)
    self.assertEqual(q[2]['package_revision'], 445)
    self.assertEqual(q[3]['package_scope'], 'test_package_3')

  def test_110_select_population_queue_unprocessed(self):
    self._populate_with_test_objects()
    q = pasta_gmn_adapter.app.sql.select_population_queue_uncompleted()
    self.assertEqual(len(q), 4)

  def test_120_select_population_queue_all(self):
    self._populate_with_test_objects()
    q = pasta_gmn_adapter.app.sql.select_population_queue_all()
    self.assertEqual(len(q), 4)

  def test_130_insert_status_error(self):
    self._populate_with_test_objects()
    package_id = pasta_gmn_adapter.app.sql.select_population_queue_all()[1]['task_id']
    with pytest.raises(Exception):
      pasta_gmn_adapter.app.sql.insert_process_status(
        package_id, '_test_status', 404, 'test_return_body'
      )

  def test_140_insert_status_completed(self):
    self._populate_with_test_objects()
    package_id = pasta_gmn_adapter.app.sql.select_population_queue_all()[1]['task_id']
    pasta_gmn_adapter.app.sql.insert_process_status(
      package_id, 'completed', 200, 'OK'
    )
    q = pasta_gmn_adapter.app.sql.select_population_queue_uncompleted()
    self.assertEqual(len(q), 3)

  def test_150_insert_status_error(self):
    self._populate_with_test_objects()
    package_id = pasta_gmn_adapter.app.sql.select_population_queue_all()[1]['task_id']
    pasta_gmn_adapter.app.sql.insert_process_status(
      package_id, 'error', 404, 'test_return_body'
    )
    q = pasta_gmn_adapter.app.sql.select_process_status_by_package_id(
      'test_package_2', 333, 444
    )
    self.assertEqual(len(q), 2)
    self.assertEqual(q[0]['status'], 'new')
    self.assertEqual(q[0]['return_code'], 0)
    self.assertEqual(q[0]['return_body'], '')

    self.assertEqual(q[1]['status'], 'error')
    self.assertEqual(q[1]['return_code'], 404)
    self.assertEqual(q[1]['return_body'], 'test_return_body')

  def test_160_select_latest_package_revision(self):
    self._populate_with_test_objects()
    self.assertEqual(
      pasta_gmn_adapter.app.sql.select_latest_package_revision(
        'test_package_2', 333
      ), 445
    )
    self.assertTrue(
      pasta_gmn_adapter.app.sql.
      select_latest_package_revision('test_package_2', 334) is None
    )
    self.assertTrue(
      pasta_gmn_adapter.app.sql.
      select_latest_package_revision('non_existing_package', 333) is None
    )


#
#
# class TestDataPackageManagerClient(django.test.TestCase):
#   @classmethod
#   def setUpClass(cls):
#     cls.c = pasta_gmn_adapter.app.data_package_manager_client.DataPackageManagerClient()
#
#   @classmethod
#   def tearDownClass(cls):
#     pass
#
#   def test_100_initialize(self):
#     pass
#
#
# class TestDataEMLAccess(django.test.TestCase):
#   @classmethod
#   def setUpClass(cls):
#     cls.e = pasta_gmn_adapter.api_types.eml_access.EMLAccess(TEST_EML_ACCESS_XML)
#
#   @classmethod
#   def tearDownClass(cls):
#     pass
#
#   def test_100_initialize(self):
#     pass
#
#   def test_200_eml_as_dataone(self):
#     d = self.e.get_as_dataone_rules()
#     self.assertTrue(isinstance(d, d1_common.types.dataoneTypes.AccessPolicy))
