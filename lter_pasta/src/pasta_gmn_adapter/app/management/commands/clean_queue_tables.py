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
"""Clean completed items from the population queue.

All but the latest version of a package scope/identifier can be deleted. The very latest
version must be preserved in order for the adapter to know which object to update.
"""
import argparse
import logging

import django.core.management.base
import django.db

import pasta_gmn_adapter.app.management.commands._util as util


class Command(django.core.management.base.BaseCommand):
    def _init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.description = __doc__
        parser.formatter_class = argparse.RawDescriptionHelpFormatter
        parser.add_argument("--debug", action="store_true", help="Debug level logging")

    def handle(self, *args, **options):
        util.log_setup(options["debug"])
        util.exit_if_other_instance_is_running(__name__)
        logging.info("Running management command: {}".format(__name__))

        for (
            package_scope,
            package_identifier,
            latest_revision,
        ) in select_all_latest_revisions():
            print("{}.{}.{}".format(package_scope, package_identifier, latest_revision))
            deleted_package_count = delete_all_but_latest_revision(
                package_scope, package_identifier, latest_revision
            )
            print("Deleted earlier revisions: {}".format(deleted_package_count))


def select_all_latest_revisions():
    """Select the package scope, identifier and latest revision for each package
    """
    cursor = django.db.connection.cursor()
    cursor.execute(
        """
    select package_scope, package_identifier, max(package_revision) latest_revision 
    from adapter_population_queue q 
    join adapter_population_queue_package_scope s on s.id = q.package_scope_id 
    group by package_scope, package_identifier
    order by package_scope, package_identifier
    ;
    """
    )
    return cursor


def delete_all_but_latest_revision(package_scope, package_identifier, latest_revision):
    cursor = django.db.connection.cursor()
    cursor.execute(
        """
    delete from adapter_population_queue q
    where package_scope_id = (
        select id from adapter_population_queue_package_scope where package_scope = %s
    )
    and package_identifier = %s
    and package_revision < %s
    ;
    """,
        [package_scope, package_identifier, latest_revision],
    )
    return cursor.rowcount
