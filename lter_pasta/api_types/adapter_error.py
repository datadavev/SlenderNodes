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

'''
:mod:`adapter_error`
====================

:Synopsis:
  - Native object for holding an adapter exception.
  - XML serialization and deserialization of adapter exception.
:Author:
  Roger Dahl
'''

# Stdlib.
import httplib
import StringIO

# D1.
import d1_common.util


DEFAULT_HTTP_ERROR_STATUS_CODE = httplib.BAD_REQUEST


class AdapterError(Exception):
  @d1_common.util.utf8_to_unicode
  def __init__(self, description, trace=None, package_id=None, http_status_code=DEFAULT_HTTP_ERROR_STATUS_CODE):
    self.description = description
    self.trace = trace
    self.package_id = package_id
    self.http_status_code = http_status_code


  def __str__(self):
    msg = StringIO.StringIO()
    msg.write(u'AdapterError:\n')
    msg.write(u'description: {0}\n'.format(self.description))
    msg.write(u'trace: {0}\n'.format(str(self.trace)))
    msg.write(u'package_id: {0}\n'.format(self.package_id))
    msg.write(u'http_status_code: {0}\n'.format(self.http_status_code))    
    # The unit test framework that comes with Python 2.6 has a bug that has been
    # fixed in later versions. http://bugs.python.org/issue8313. The bug causes
    # stack traces containing Unicode to be shown as "unprintable". So, for now,
    # string representations of exceptions are forced to ascii, where non-ascii
    # characters are replaced with a box.
    return unicode(msg.getvalue()).encode("utf-8")


  def friendly_format(self):
    '''Serialize to a format more suitable for displaying to end users.
    '''
    return 'Error: {0}'.format(self.description)


  def serialize(self):
    adapter_error_pyxb = pasta_gmn_adapter.types.generated.pasta_gmn_adapter_types.adapterError()
    adapter_error_pyxb.description = self.description
    adapter_error_pyxb.trace = self.trace
    adapter_error_pyxb.package_id = self.package_id
    return adapter_error_pyxb.toxml()
