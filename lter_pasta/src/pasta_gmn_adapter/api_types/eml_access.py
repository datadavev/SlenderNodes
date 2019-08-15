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
:mod:`eml_access`
=================

:Synopsis:
  - Native object for holding an EML access type.
  - XML serialization and deserialization of an EML access type.
:Author:
  Roger Dahl
"""

import logging

import pyxb

import d1_common.types.dataoneTypes

import pasta_gmn_adapter.api_types.generated.eml_access


# Raised when the Data Package Manager returns an error response.
class EMLAccessException(Exception):
  def __init__(self, msg):
    self.msg = msg
    self.status = 'eml_access_rules_exception'
    self.body = ''

  def __str__(self):
    return ('EMLAccessException: {0}'.format(self.msg))


#=============================================================================


class EMLAccess(object):
  def __init__(self, eml_access_xml=None):
    if eml_access_xml is not None:
      self._eml_access = self.deserialize(eml_access_xml)

  def deserialize(self, eml_access_xml):
    try:
      return pasta_gmn_adapter.api_types.generated.eml_access.CreateFromDocument(
        eml_access_xml
      )
    except pyxb.BadDocumentError:
      logging.exception('Invalid document. Exception:')
      raise

  def serialize(self):
    return self._eml_access.toxml()

  def _raise_if_access_rules_not_supported_by_dataone(self):
    '''DataONE is more limited than EML in which access rules are supported.'''
    # DataONE does not support deny rules.
    if len(self._eml_access.deny) > 0:
      raise EMLAccessException(
        'Access rules contain one or more deny rules, which are unsupported by DataONE'
      )

  def get_as_dataone_rules(self):
    # DataONE's allow rules are almost the same as EML. The principal in EML is
    # the subject in DataONE. EML supports "all" as a synonym of
    # "changePermission". The "all" synonym is not supported in DataONE, so it
    # is translated to "changePermission".
    accessPolicy = d1_common.types.dataoneTypes.accessPolicy()
    for a in self._eml_access.allow:
      accessRule = d1_common.types.dataoneTypes.AccessRule()
      for p in a.principal:
        accessRule.subject.append(p)
      for e in a.permission:
        permission_str = str(e)
        if permission_str == 'all':
          permission_str = 'changePermission'
        permission = d1_common.types.dataoneTypes.Permission(permission_str)
        accessRule.permission.append(permission)
      accessPolicy.append(accessRule)
    return accessPolicy
