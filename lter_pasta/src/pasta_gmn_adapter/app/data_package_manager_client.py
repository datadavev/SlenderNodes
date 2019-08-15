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
""":mod:`Module data_package_manager_client`
============================================

:Synopsis:
  This module implements a client for the PASTA Package Manager REST API.
:Author:
  Roger Dahl
"""

import base64
import http.client
import io
import logging
import pprint
import urllib.parse
import xml.etree.ElementTree as ET

import requests.structures

import d1_common.const
import d1_common.url
import d1_common.util

import d1_client.baseclient

import pasta_gmn_adapter.api_types.eml_access
from pasta_gmn_adapter import api_types
from pasta_gmn_adapter import settings

NAMESPACE_DICT = {
  'eml': 'eml://ecoinformatics.org/eml-2.1.1',
  'd1v1': 'http://ns.dataone.org/service/types/v1'
}


# Raised when the Data Package Manager returns an error response.
class DataPackageManagerException(Exception):
  def __init__(self, msg, status, body):
    self.msg = msg
    self.status = status
    self.body = body

  def __str__(self):
    return (
      'DataPackageManagerException: message({0}) status({1}) body({2})'
      .format(self.msg, self.status, self.body)
    )


#=============================================================================


class DataPackageManagerClient(
    d1_client.baseclient.DataONEBaseClient,):
  """PASTA Data Package Manager web service API methods that are used by the
  PASTA GMN Adapter.

  Error responses are translated into exceptions.
  """

  def __init__(self, **kwargs):
    """Connect to the PASTA Data Package Manager web service API.
    """
    base_url = kwargs.pop('base_url', settings.PASTA_BASE_URL)
    logging.debug('PASTA BaseURL: {0}'.format(base_url))

    add_basic_auth_header = kwargs.pop('add_basic_auth_header', True)

    # Workaround for issue where PASTA appears to return an invalid response
    # after the connection has been reused many times (only happens for
    # packages with many data entities).
    kwargs.setdefault('headers', requests.structures.CaseInsensitiveDict())
    kwargs['headers'].setdefault('Connection', 'close')
    kwargs.setdefault('user_agent', settings.PASTA_GMN_ADAPTER_USER_AGENT)
    kwargs.setdefault('user_agent', settings.PASTA_GMN_ADAPTER_USER_AGENT)

    # Debug: Disable server side certificate verification
    kwargs.setdefault('verify_tls', False)

    if add_basic_auth_header:
      kwargs['headers'].update((self._mk_http_basic_auth_header(),))

    logging.debug('DataPackageManagerClient() kwargs={}'.format(pprint.pformat(kwargs)))

    super(DataPackageManagerClient, self).__init__(base_url, **kwargs)

  def _get_api_version_path_element(self):
    """Override the default API version selection for PASTA"""
    return ''

  def _mk_http_basic_auth_header(self):
    return (
      'Authorization', 'Basic {0}'.format(
        base64.standard_b64encode(
          '{0}:{1}'.format(
            settings.PASTA_API_USERNAME, settings.PASTA_API_PASSWORD
          ).encode('utf-8')
        ).decode('utf-8')
      )
    )

  def _parse_url(self, url):
    parts = urllib.parse.urlsplit(url)
    if parts.port is None:
      port = 443 if parts.scheme == 'https' else 80
    else:
      port = parts.port
    host = parts.netloc.split(':')[0]
    return parts.scheme, host, port, parts.path, parts.query, parts.fragment

  def GET_URL(self, url, **kwargs):
    return self._session.request('GET', url, **kwargs)

  def HEAD_URL(self, url, **kwargs):
    return self._session.request('HEAD', url, **kwargs)

  def POST_URL(self, url, **kwargs):
    return self._session.request('POST', url, **kwargs)

  # ----------------------------------------------------------------------------
  # Response handling.
  # ----------------------------------------------------------------------------

  # When expecting boolean response:
  #
  #   If status is 200:
  #     -> Ignore content_type and return True
  #
  #   If status is NOT 200:
  #     -> ERROR
  #
  # When expecting an XML document:
  #
  #   If status is 200 and content_type is "application/xml":
  #     - Return XML document
  #   Else:
  #     - Raise exception with body of response as error message.
  #
  # When expecting a text document:
  #
  #   If status is 200 and content_type is "text/plain":
  #     - Return text document.
  #   Else:
  #     - Raise exception with body of response as error message.

  def _get_data_redirect_header(self, redirect_url):
    urlsplit = urllib.parse.urlparse(redirect_url)
    full_path = urlsplit.path + '?' + urlsplit.query
    conn = http.client.HTTPConnection(urlsplit.netloc)
    conn.request('HEAD', full_path)
    return conn.getresponse()

  def _read_and_capture(self, response):
    response_body = response.text
    return response_body

  def _raise_data_package_manager_exception(self, msg, response):
    response_body = self._read_and_capture(response)
    raise DataPackageManagerException(msg, response.status_code, response_body)

  def _raise_service_failure_invalid_content_type(self, response):
    msg = io.StringIO()
    msg.write(
      'Data Package Manager responded with a valid status code but '
      'failed to include the expected Content-Type\n'
    )
    msg.write('Status code: {0}\n'.format(response.status_code))
    msg.write('Content-Type: {0}\n'.format(response.headers['Content-Type']))
    self._raise_data_package_manager_exception(msg.getvalue(), response)

  def _content_type_is_xml(self, response):
    return d1_common.util.get_content_type(
      response.headers['Content-Type'] in d1_common.const.CONTENT_TYPE_XML_MEDIA_TYPES
    )

  def _content_type_is_text(self, response):
    return d1_common.util.get_content_type(response.headers['Content-Type']
                                           ) == 'text/plain'

  def _status_is_200_ok(self, response):
    return response.status_code == http.HTTPStatus.OK

  def _status_is_307_temporary_redirect(self, response):
    return response.status_code == http.HTTPStatus.TEMPORARY_REDIRECT

  def _read_boolean_response(self, response):
    if self._status_is_200_ok(response):
      self._read_and_capture(response)
      return True
    self._raise_exception(response)

  def _read_xml_response(self, response):
    if not self._status_is_200_ok(response):
      return self._raise_data_package_manager_exception('Error', response)
    if not self._content_type_is_xml(response):
      self._raise_service_failure_invalid_content_type(response)
    return response.text

  def _read_text_response(self, response):
    if not self._status_is_200_ok(response):
      return self._raise_data_package_manager_exception('Error', response)
    if not self._content_type_is_text(response):
      self._raise_service_failure_invalid_content_type(response)
    return response.text

  def _read_raw_response(self, response):
    if not self._status_is_200_ok(response):
      return self._raise_data_package_manager_exception('Error', response)
    return response.text

  def _read_header_response(self, response):
    if not self._status_is_200_ok(response):
      return self._raise_data_package_manager_exception('Error', response)
    # Must empty the response body to ready the connection for another
    # request. Since a HEAD request was used, the body should be empty.
    response.text
    return response.headers

  def _read_eml_access_response(self, response):
    if not self._status_is_200_ok(response):
      return self._raise_data_package_manager_exception('Error', response)
    eml_access_xml_doc = response.text
    return pasta_gmn_adapter.api_types.eml_access.EMLAccess(eml_access_xml_doc)

  # ----------------------------------------------------------------------------
  # Misc.
  # ----------------------------------------------------------------------------

  # def _rest_url(self, path_format, **args):
  #   for k in list(args.keys()):
  #     args[k] = d1_common.url.encodePathElement(args[k])
  #   path = path_format % args
  #   url = '/' + d1_common.url.joinPathElements(self.version, path)
  #   return url

  # ----------------------------------------------------------------------------
  # Data Package Manager web service API wrappers
  # ----------------------------------------------------------------------------

  # List Data Entities

  def list_data_entities(self, package_id):
    """List the entity IDs of the data members of a package"""
    response = self.list_data_entities_response(package_id)
    identifiers = self._read_text_response(response)
    return sorted(identifiers.strip().split('\n'))

  def list_data_entities_response(self, package_id):
    return self.GET([
      'data', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision())
    ])

  # List Data Package Identifiers

  def list_data_package_identifiers(self, scope):
    response = self.list_data_package_identifiers_response(scope)
    identifiers = self._read_text_response(response)
    return sorted(map(int, identifiers.strip().split('\n')))

  def list_data_package_identifiers_response(self, scope):
    return self.GET(['eml', scope])

  # List Data Package Revisions

  def list_data_package_revisions(self, scope, identifier):
    response = self.list_data_package_revisions_response(scope, identifier)
    identifiers = self._read_text_response(response)
    return sorted(map(int, identifiers.strip().split('\n')))

  def list_data_package_revisions_response(self, scope, identifier):
    return self.GET(['eml', scope, str(identifier)])

  # List Data Package Scopes

  def list_data_package_scopes(self):
    response = self.list_data_package_scopes_response()
    identifiers = self._read_text_response(response)
    return sorted(identifiers.strip().split('\n'))

  def list_data_package_scopes_response(self):
    return self.GET('eml')

  # List Deleted Data Packages

  def list_deleted_packages(self):
    response = self.list_deleted_packages_response()
    identifiers = self._read_text_response(response)
    return sorted(identifiers.strip().split('\n'))

  def list_deleted_packages_response(self):
    return self.GET(['eml', 'deleted'])

  # Read Data Entity Name

  def read_data_entity_name(self, package_id, entity_id):
    response = self.read_data_entity_name_response(package_id, entity_id)
    return self._read_raw_response(response)

  def read_data_entity_name_response(self, package_id, entity_id):
    return self.GET([
      'data', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision()), entity_id
    ])


#   # List Data Package Identifiers
#
#
#   def list_data_package_identifiers(self, package_id):
#     response = self.list_data_package_identifiers_response(package_id)
#     identifiers = self._read_text_response(response)
#     return identifiers.strip().split('\n')
#
#
#
#   def list_data_package_identifiers_response(self, package_id):
#     url = self._rest_url('eml/%(scope)s/%(identifier)s/%(revision)s',
#                          scope=package_id.scope(),
#                          identifier=str(package_id.identifier()),
#                          revision=str(package_id.revision()))
#     return self.GET(url)

# Read Data Package DOI

  def read_data_package_doi(self, package_id):
    response = self.read_data_package_doi_response(package_id)
    return self._read_text_response(response).strip()

  def read_data_package_doi_response(self, package_id):
    return self.GET([
      'doi', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision())
    ])

  # Is Authorized

  def is_authorized(self, package_id, entity_id):
    """Determine if read access to data entity is authorized"""
    response = self.is_authorized_response(package_id, entity_id)
    return self._read_text_response(response)

  def is_authorized_response(self, package_id, entity_id):
    return self.GET(['authz'], query={
      'resourceId': self.entity_uri(package_id, entity_id),
    })

  # Read Data Package ACL

  def read_data_package_acl(self, package_id):
    response = self.read_data_package_acl_response(package_id)
    return self._read_eml_access_response(response)

  def read_data_package_acl_response(self, package_id):
    return self.GET([
      'acl', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision())
    ])

  # Read Data Entity ACL

  def read_data_entity_acl(self, package_id, entity_id):
    response = self.read_data_entity_acl_response(package_id, entity_id)
    return self._read_eml_access_response(response)

  def read_data_entity_acl_response(self, package_id, entity_id):
    return self.GET([
      'data', 'acl', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision()), entity_id
    ])

  # Read Data Package Report ACL

  def read_quality_report_acl(self, package_id):
    response = self.read_quality_report_acl_response(package_id)
    return self._read_eml_access_response(response)

  def read_quality_report_acl_response(self, package_id):
    return self.GET([
      'report', 'acl', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision())
    ])

  # Read Metadata ACL

  def read_metadata_acl(self, package_id):
    response = self.read_metadata_acl_response(package_id)
    return self._read_eml_access_response(response)

  def read_metadata_acl_response(self, package_id):
    return self.GET([
      'metadata', 'acl', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision())
    ])

  # Read Data Entity Checksum (SHA-1)

  def read_data_entity_checksum(self, package_id, entity_id):
    response = self.read_data_entity_checksum_response(package_id, entity_id)
    return self._read_text_response(response).strip()

  def read_data_entity_checksum_response(self, package_id, entity_id):
    return self.GET([
      'data', 'checksum', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision()),
      str(entity_id)
    ])

  # Read Data Package Report Checksum (SHA-1)

  def read_data_package_report_checksum(self, package_id):
    response = self.read_data_package_report_checksum_response(package_id)
    return self._read_text_response(response).strip()

  def read_data_package_report_checksum_response(self, package_id):
    return self.GET([
      'report', 'checksum', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision())
    ])

  # Read Metadata Checksum (SHA-1)

  def read_metadata_checksum(self, package_id):
    response = self.read_metadata_checksum_response(package_id)
    return self._read_text_response(response).strip()

  def read_metadata_checksum_response(self, package_id):
    return self.GET([
      'metadata', 'checksum', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision())
    ])

  # Read Metadata Format ID

  def read_metadata_format_id(self, package_id):
    """Returns the Format ID, e.g., eml://ecoinformatics.org/eml-2.1.0
    """
    response = self.read_metadata_format_id_response(package_id)
    return self._read_text_response(response).strip()

  def read_metadata_format_id_response(self, package_id):
    return self.GET([
      'metadata', 'format', 'eml',
      package_id.scope(),
      str(package_id.identifier()),
      str(package_id.revision())
    ])

  # Get Data Entry Header

  def get_data_entry_header(self, resource_url):
    logging.info('Resource URL: {}'.format(resource_url))
    response = self.get_data_entry_header_response(resource_url)
    if self._status_is_307_temporary_redirect(response):
      temporary_url = response.headers['Location']
      response = self._get_data_redirect_header(temporary_url)
    return self._read_header_response(response)

  def get_data_entry_header_response(self, resource_url):
    return self.HEAD_URL(resource_url)

  # Read EML

  def read_eml(self, eml_url):
    response = self.read_eml_response(eml_url)
    return self._read_xml_response(response)

  def read_eml_response(self, eml_url):
    return self.GET_URL(eml_url)

  # Utils

  def read_metadata_replication_policy(self, package_id):
    """Retrieve EML doc from {eml_url}, extract and return the DataONE
    Replication Policy XML document if one exists. Else return None.
    """
    eml_url = self.metadata_url(package_id)
    eml_xml = self.read_eml(eml_url)
    tree = ET.ElementTree(ET.fromstring(eml_xml))
    root = tree.getroot()
    replication_policy_list = root.findall(
      "additionalMetadata/metadata/d1v1:replicationPolicy", NAMESPACE_DICT
    )
    if len(replication_policy_list):
      return ET.tostring(replication_policy_list[0])

  def entity_uri(self, package_id, entity_id):
    return d1_common.url.joinPathElements(
      self.base_url,
      self.encode_and_join_path_elements(
        'data', 'eml', package_id.scope(), package_id.identifier(),
        package_id.revision(), entity_id
      )
    )

  def report_uri(self, package_id):
    return d1_common.url.joinPathElements(
      self.base_url,
      self.encode_and_join_path_elements(
        'report', 'eml', package_id.scope(), package_id.identifier(),
        package_id.revision()
      )
    )

  def metadata_url(self, package_id):
    return d1_common.url.joinPathElements(
      self.base_url,
      self.encode_and_join_path_elements(
        'metadata', 'eml', package_id.scope(), package_id.identifier(),
        package_id.revision()
      )
    )

  def encode_and_join_path_elements(self, *elements):
    return d1_common.url.joinPathElements(
      *[d1_common.url.encodePathElement(e) for e in elements]
    )

  # Metadata DOIs are not yet implemented in PASTA.

  #
  #def get_metadata_doi_response(self, scope, identifier, revision):
  #  url = self._rest_url('metadata/doi/eml/%(scope)s/%(identifier)s/%(revision)s',
  #                       scope=scope, identifier=str(identifier),
  #                       revision=str(revision))
  #  print url
  #  return self.GET(url)
  #
  #
  #
  #def get_metadata_doi(self, scope, identifier, revision):
  #  response = self.get_metadata_doi_response(scope, identifier, revision)
  #  return self._read_text_response(response).strip()
  #
  #
  #
  #def get_data_package_doi_response(self, scope, identifier, revision, entity_id):
  #  url = self._rest_url('data/doi/%(scope)s/%(identifier)s/%(revision)s/%(entity_id)s',
  #                       scope=scope, identifier=str(identifier),
  #                       revision=str(revision), entity_id=entity_id)
  #  return self.GET(url)
  #
  #
  #
  #def get_data_package_doi(self, scope, identifier, revision, entity_id):
  #  response = self.get_data_package_doi_response(scope, identifier, revision, entity_id)
  #  return self._read_text_response(response).strip()
