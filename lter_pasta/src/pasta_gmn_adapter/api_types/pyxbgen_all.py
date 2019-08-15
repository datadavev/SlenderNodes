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

# Generate PyXB binding classes from schemas.

import optparse
import os


def main():
  # Command line opts.
  parser = optparse.OptionParser()
  # The default location for the schemas relative to d1_common_python if both were checked out as part of cicore.
  parser.add_option(
    '-s', '--schemas', dest='schemas_path', action='store', type='string',
    default='./schemas'
  )
  parser.add_option(
    '-t', '--bindings', dest='bindings_path', action='store', type='string',
    default='./generated'
  )
  parser.add_option(
    '-p', '--process', dest='process_schemas', action='store', type='string',
    default='pasta_gmn_adapter_types.xsd;eml-access.xsd'
  )

  (opts, args) = parser.parse_args()

  if not os.path.exists(opts.bindings_path):
    print('The destination folder for the bindings does not exist.')
    print('This script should be run from ./api_types')
    exit()

  process_schemas_list = opts.process_schemas.split(';')

  for schema_filename in process_schemas_list:
    schema_name = os.path.splitext(schema_filename)[0].replace('-', '_')
    print('Processing: {0}'.format(schema_name))
    schema_path = os.path.join(opts.schemas_path, schema_filename)
    binding_path = os.path.join(
      opts.bindings_path,
      os.path.splitext(schema_filename)[0] + '.py'
    )

    # pyxbgen sometimes does not want to overwrite existing binding classes.
    try:
      os.unlink(binding_path)
    except OSError:
      pass

    # Run pyxbgen.
    args = [
      '--binding-root=\'{0}\''.format(opts.bindings_path),
      '-u \'{0}\' -m \'{1}\''.format(schema_path, schema_name),
    ]
    #args.append('--location-prefix-rewrite=\'https://repository.dataone.org/software/cicore/trunk/schemas/={0}\''.format(opts.schema_path))
    # Note: If we split the schema out to multiple files, pyxbgen is still
    # run only once, but with multiple sets of -u and -m.
    cmd = 'pyxbgen {0}'.format(' '.join(args))
    print(cmd)
    os.system(cmd)


if __name__ == '__main__':
  main()
