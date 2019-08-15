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
:mod:`sql`
==========

:Synopsis:
  Database specific layer.

  This module is used instead of models.py and Django's ORM. It acts on a
  database created with the pasta_gmn_adapter.sql script.

:Author:
  Roger Dahl

:Requires:
  PostgreSQL >= 9.1.
"""
import django.db

VCHAR_LENGTH = 2048


def dict_fetch_all(cursor):
  """Return all rows from a cursor as a dict."""
  return [
    dict(list(zip([col[0] for col in cursor.description], row)))
    for row in cursor.fetchall()
  ]


def insert_population_queue_item(scope, identifier, revision):
  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    insert into adapter_population_queue_package_scope (package_scope)
    select %s where not exists (
      select id from adapter_population_queue_package_scope where package_scope = %s
    );
    """,
    [scope, scope]
  )

  cursor.execute(
    """
    insert into adapter_population_queue
    (package_scope_id, package_identifier, package_revision, "timestamp")
    select id, %s, %s, now() from adapter_population_queue_package_scope
    where package_scope = %s
    returning id;
    """,
    [int(identifier), int(revision), scope]
  )

  queue_id = cursor.fetchone()[0]

  insert_process_status(queue_id, 'new')

  return queue_id


def select_population_queue_with_latest_status():
  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    select apq.id, apqps.package_scope, apq.package_identifier,
      apq.package_revision, apss.status, aps.return_code, substring(apsrb.return_body from 1 for 256) as return_body,
      apq.timestamp as timestamp_queued, aps.timestamp as timestamp_processed
    from adapter_population_queue apq
    left join adapter_population_queue_package_scope apqps on (apq.package_scope_id = apqps.id)
    left join adapter_process_status aps on (aps.population_queue_item_id = apq.id)
    left join adapter_process_status_status apss on (apss.id = aps.status_id)
    left join adapter_process_status_return_body apsrb on (apsrb.id = aps.return_body_id)
    where (
      aps.timestamp = (
        select max(timestamp)
        from adapter_process_status aps
        where aps.population_queue_item_id = apq.id
      )
      or aps.timestamp is null
    )
    order by package_scope, package_identifier, package_revision
  ;
  """
  )

  return dict_fetch_all(cursor)


def select_population_queue_with_latest_status_uncompleted():
  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    select apq.id, apqps.package_scope, apq.package_identifier,
      apq.package_revision, apss.status, aps.return_code, substring(apsrb.return_body from 1 for 256) as return_body,
      apq.timestamp as timestamp_queued, aps.timestamp as timestamp_processed
    from adapter_population_queue apq
    left join adapter_population_queue_package_scope apqps on (apq.package_scope_id = apqps.id)
    left join adapter_process_status aps on (aps.population_queue_item_id = apq.id)
    left join adapter_process_status_status apss on (apss.id = aps.status_id)
    left join adapter_process_status_return_body apsrb on (apsrb.id = aps.return_body_id)
    where (
      aps.timestamp = (
        select max(timestamp)
        from adapter_process_status aps
        where aps.population_queue_item_id = apq.id
      )
      or aps.timestamp is null
    )
    and apq.id not in (
      select population_queue_item_id
      from adapter_process_status aps
      join adapter_process_status_status apss on (apss.id = aps.status_id)
      where apss.status in ('completed', 'private', 'permanent_error')
    )
    order by package_scope, package_identifier, package_revision
  ;
  """
  )

  return dict_fetch_all(cursor)


def select_status(population_queue_id):
  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    select * from adapter_process_status aps
    join adapter_process_status_status apss on (apss.id = aps.status_id)
    join adapter_process_status_return_body apsrb on (apsrb.id = aps.return_body_id)
    where aps.population_queue_item_id = %s
    order by aps.timestamp asc;
    ;
  """,
    [population_queue_id]
  )

  return dict_fetch_all(cursor)


def select_statistics():
  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    select status, count(*)
    from adapter_process_status aps
    join adapter_process_status_status apss on (apss.id = aps.status_id)
    where aps.timestamp = (
      select max(timestamp)
      from adapter_process_status aps2
      where aps2.population_queue_item_id = aps.population_queue_item_id
    )
    or aps.timestamp is null
    group by status
    ;
  """
  )

  return dict_fetch_all(cursor)


def select_population_queue_all():
  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    select *, apq.id as task_id, (select sub_apss.status
               from adapter_process_status sub_aps
                    left join adapter_process_status_status sub_apss
                        on (sub_apss.id = sub_aps.status_id)
                    left join adapter_process_status_return_body sub_apsrb
                        on (sub_apsrb.id = sub_aps.return_body_id)
               where sub_aps.population_queue_item_id = apq.id
                 and sub_aps."timestamp" = (select max("timestamp")
                                            from adapter_process_status
                                            where population_queue_item_id = apq.id
                                            ))
    from adapter_population_queue apq
         left join adapter_population_queue_package_scope apqps
             on (apq.package_scope_id = apqps.id)
  """
  )

  return dict_fetch_all(cursor)


# select *, (
#   select sub_aps."timestamp", sub_apss.status, sub_aps.return_code, sub_apsrb.return_body
#   from adapter_process_status sub_aps
#   left join adapter_process_status_status sub_apss on (sub_apss.id = sub_aps.status_id)
#   left join adapter_process_status_return_body sub_apsrb on (sub_apsrb.id = sub_aps.return_body_id)
#   where sub_aps."timestamp" = (
#     select max("timestamp")
#     from adapter_process_status
#     where population_queue_item_id = apq.id
#   )
# )
# from adapter_population_queue apq
# left join adapter_population_queue_package_scope apqps on (apq.package_scope_id = apqps.id)
# ;

#     ; select apq.*, apq.id as task_id, apqps.*, (
# apq.timestamp as timestamp_queued, aps.timestamp as timestamp_processed


def select_population_queue_uncompleted():
  """Select all the population tasks that have not yet been successfully
  processed."""
  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    select apq.id, package_scope, package_identifier, package_revision, "timestamp"
    from adapter_population_queue apq
    left join adapter_population_queue_package_scope apqps on (apq.package_scope_id = apqps.id)
    where apq.id not in (
      select population_queue_item_id
      from adapter_process_status aps
      join adapter_process_status_status apss on (apss.id = aps.status_id)
      where apss.status in ('completed', 'private', 'permanent_error')
    )
    order by package_scope, package_identifier, package_revision;
  """
  )

  return dict_fetch_all(cursor)


def select_latest_package_revision(scope, identifier):
  """If one or more packages with the given scope and identifier exist, return
  the revision of the latest package. Else, return None. Only the latest package
  that has also been successfully completed is returned because packages that
  have not been inserted into GMN cannot be updated."""
  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    select id from adapter_population_queue_package_scope where package_scope = %s
  ;
  """,
    [scope]
  )

  try:
    scope_id = cursor.fetchone()[0]
  except TypeError:
    return None

  cursor.execute(
    """
    select max(package_revision) from adapter_population_queue
    where package_scope_id = %s and package_identifier = %s
    and id in (
      select population_queue_item_id
      from adapter_process_status aps
      join adapter_process_status_status apss on (apss.id = aps.status_id)
      where apss.status in ('completed')
    )
  ;
  """,
    [scope_id, identifier]
  )

  return cursor.fetchone()[0]


def insert_process_status(task_id, status, return_code=0, return_body=''):
  """Insert the results from processing one object. The result may be a
  successful completion or an error.

  :status: a controlled list of processing status codes:
    'new', 'completed', 'private', 'error', 'permanent_error'
  :return_code: integer error code
  :return_body: error string
  """

  if status not in ('new', 'completed', 'private', 'error', 'permanent_error'):
    raise Exception('Invalid status: {}'.format(status))

  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    select id from adapter_process_status_status where status = %s
    """,
    [status]
  )
  try:
    status_id = cursor.fetchone()[0]
  except TypeError:
    cursor.execute(
      """
      insert into adapter_process_status_status (status)
      values (%s)
      returning id;
      """,
      [status]
    )
    status_id = cursor.fetchone()[0]

  cursor.execute(
    """
    select id from adapter_process_status_return_body where return_body = %s
    """,
    [return_body]
  )
  try:
    return_body_id = cursor.fetchone()[0]
  except TypeError:
    cursor.execute(
      """
      insert into adapter_process_status_return_body (return_body)
      values (%s)
      returning id;
      """,
      [return_body]
    )
    return_body_id = cursor.fetchone()[0]

  cursor.execute(
    """
    insert into adapter_process_status (population_queue_item_id, "timestamp",
      status_id, return_code, return_body_id)
    values (%s, now(), %s, %s, %s)
    ;
    """,
    [task_id, status_id, return_code, return_body_id]
  )

  return status_id


def select_process_status_by_package_id(scope, identifier, revision):
  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    select apss.status, return_code, apsrb.return_body
    from adapter_process_status aps
    left join adapter_process_status_status apss on (apss.id = aps.status_id)
    left join adapter_process_status_return_body apsrb on (apsrb.id = aps.return_body_id)
    left join adapter_population_queue apq on (apq.id = aps.population_queue_item_id)
    left join adapter_population_queue_package_scope apqps on (apqps.id = apq.package_scope_id)
    where apqps.package_scope = %s
    and apq.package_identifier = %s
    and apq.package_revision = %s
    ;
    """,
    [scope, identifier, revision]
  )

  return dict_fetch_all(cursor)


def clear_database():
  cursor = django.db.connection.cursor()

  cursor.execute(
    """
    delete from adapter_process_status;
    delete from adapter_process_status_status;
    delete from adapter_process_status_return_body;
    delete from adapter_population_queue;
    delete from adapter_population_queue_package_scope;
    ;
    """
  )
