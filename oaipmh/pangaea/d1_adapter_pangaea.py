"""
________________________________________________________________________________________________________________________

d1_adapter_pangea.py acts as both an OAI-PMH harvester client and an adapter bridging harvested content into an
installation of DataONE Generic Member Node (GMN). This is the main script which handles OAI-PMH querying and processing
while an accompanying script, d1_client_manager.py, is required for managing the actual operations upon data into GMN
using the Python library implementation of DataONE GMN. The script is designed to be reusable for any OAI-PMH server with
very little modification. Server-specific configurations are defined at the top.

___________________________________________________________
"""


import logging
logging.basicConfig(filename='adapter-errors.log',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.ERROR)
logger = logging.getLogger(__name__)

import os
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import datetime
import pytz
# D1 functionality found here:
import d1_client_manager_pangaea


file_name = 'OAI-PMH_harvest.log'
if os.path.exists(file_name):
    file_action = 'a' # append if already exists
else:
    file_action = 'w' # make a new file if not

# ----------------------------------------------------------------------------------------------------------------------

OAIPMH_BASE_URL = 'https://ws.pangaea.de/oai/provider'
SCIMETA_ELEMENT = '{http://www.isotc211.org/2005/gmd}MD_Metadata'
#For dc would be something like SCIMETA_ELEMENT = '{http://www.openarchives.org/OAI/2.0/oai_dc/}oai_dc'
MN_BASE_URL = 'https://pangaea-orc-1.dataone.org/mn'
CERT = './certs/urn_node_PANGAEA.crt'    # Should be either D1 generated cert (Prod) or local CA generated (Test)
KEY = './certs/urn_node_PANGAEA.key'  # Either D1 generated cert key (Prod) or local CA generated (Test)
SYSMETA_DICT = \
    {'submitter': 'urn:node:PANGAEA',
     'rightsholder': 'urn:node:PANGAEA',
     'authoritativeMN': 'urn:node:mnTestPANGAEA',  # Use your node's DataONE URI
     'originMN': 'urn:node:PANGAEA',  # Use your node's DataONE URI
     'formatId_custom': 'http://www.isotc211.org/2005/gmd-pangaea' # should be consistent w/ scimeta_element format
      }
created_count = 0  # global incrementer for metadata records harvested.
updated_count = 0  # global incrementer for records updated each time program is run
archived_count = 0 # global incrementer for records archived in a given run
skipped_exists_count = 0
skipped_deleted_count = 0

start = 1  # is this the initial query request?
rtoken = None
last_harvest_time = ''


# ----------------------------------------------------------------------------------------------------------------------
def main():
  global rtoken
  global last_harvest_time
  requests.packages.urllib3.disable_warnings()
  client_mgr = d1_client_manager_pangaea.D1ClientManager(MN_BASE_URL, CERT, KEY, SYSMETA_DICT)
  harvester = OAIPMH_Harvester(OAIPMH_BASE_URL)
  last_harvest_time = client_mgr.get_last_harvest_time()  # get date most recent sysmetamodified as start of timeslice
  while (start == 1) or (start == 0 and rtoken is not None):
    record_list = harvester.get_records(harvester.define_params())
    if record_list is not None:
      rtoken_record = record_list.find('{http://www.openarchives.org/OAI/2.0/}resumptionToken')
      if rtoken_record is None:
        rtoken = None
      else:
        rtoken = rtoken_record.text
        record_list.remove(rtoken_record) # excludes rtoken from the processing that happens to rest of results
      for metadata_record in record_list:
        harvester.process_record(record=metadata_record, client_mgr=client_mgr)
    else:
        pass

  tracking_log = open(file_name, file_action)
  tracking_log.write(datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S") +
    ', New Records Loaded: {}, Records Updated: {}, Records archived: {}, Deleted skipped: {}, existing skipped: {}.\n'
                     .format(created_count, updated_count, archived_count, skipped_deleted_count, skipped_exists_count))
  tracking_log.close()


# ----------------------------------------------------------------------------------------------------------------------
class OAIPMH_Harvester:
  def __init__(self, baseURL):
    """
    :param baseURL: The OAI-PMH provider's base URL, not to be confused with the base URL configured for GMN.
    """
    self.baseURL = baseURL

# ----------------------------------------------------------------------------------------------------------------------
  def define_params(self):
    """
    OAI-PMH query format depends on whether this is the initial or a subsequent oai-pmh request. After initial params
    have been defined once, start is reset to false. Next time function is called, resumption token parameters
    will be returned.

    :returns: A dictionary containing parameters that will be used to construct the appropriate OAI-PMH request.
    """
    global start
    global rtoken
    if start == 1:
      # It is an option to uncomment this version and comment out harvest based timeslice params
      #params = {'verb': 'ListRecords',
      #          'metadataPrefix': 'iso19139',
      #          'from': '2000-01-01T00:00:00Z',
      #          'until': '2018-01-31T23:59:59Z'}
      params = {'verb': 'ListRecords',
                'metadataPrefix': 'iso19139',
                'from': last_harvest_time}
      start = 0

    else:
      params = {'verb': 'ListRecords',
                'resumptionToken': rtoken}
      rtoken = None
    return params

# ----------------------------------------------------------------------------------------------------------------------
  def get_records(self, parameters):
    """Accepts request parameters and uses them to construct an OAI-PMH ListRecords request, the results of which are
    extracted and then returned to the main program.

    :param parameters: The request parameters are defined in get_params().

    :return: A list of records if a OAI-PMH request with 200 http response returns it. Otherwise, a successful http request that has no matching results will end up returning None to the main program."""

    headers = {
      'User-Agent': 'DataONE Adapter for OAI-PMH Harvest',
      'From': 'mihli1@utk.edu'}
    try:
      r = requests.get(url=self.baseURL, params=parameters, headers=headers)
      if r.status_code == requests.codes.ok:
        root = ET.fromstring(r.content)
        record_list = root.find('{http://www.openarchives.org/OAI/2.0/}ListRecords')
        return record_list # If element not found, returns none (such as if <error code="noRecordsMatch"/>)
      else:
        logging.error('Request failed: {}'.format(r.url))
    except Exception, e:
      logging.error('Request failed: {}'.format(e))


# ----------------------------------------------------------------------------------------------------------------------
  def process_record(self, client_mgr, record):
    """Determines how to handle each science metadata record returned in the OAI-PMH harvest, whether that is to ignore
    it, or to archive, create, or update it in GMN.

    :param client_mgr: An instance of d1_client_manager() (See d1_client_manager_pangaea.py) which handles dataone client related functionality.
    :param record: The complete OAI-PMH record returned in the list of OAI-PMH query results."""

    global created_count
    global updated_count
    global archived_count
    global skipped_exists_count
    global skipped_deleted_count

    # If this is a record with deleted status, check if already exists in GMN. If does not exist, then ignore. But
    # if it does already exist in GMN, then it should be archived
    if 'status' in record.find('{http://www.openarchives.org/OAI/2.0/}header').attrib:
      if record.find('{http://www.openarchives.org/OAI/2.0/}header').attrib['status'] == 'deleted':
        identifier = record.find('{http://www.openarchives.org/OAI/2.0/}header'). \
          find('{http://www.openarchives.org/OAI/2.0/}identifier').text.replace(
          'oai:pangaea.de:', '')
        checkExistsDict = client_mgr.check_if_identifier_exists(identifier)
        if checkExistsDict['outcome'] == 'yes':
          if client_mgr.archive_science_metadata(checkExistsDict['current_version_pid']):
            archived_count += 1  # track the number of successfully archived objects
        else: # record that a deleted record in OAI-PMH resultset was skipped over because not already in GMN
          skipped_deleted_count += 1

    # Otherwise status is not deleted, so parse record ID, date, and metadata contents.
    # Then check if this identifier already exists in GMN.
    else:
      try:
        identifier = record.find('{http://www.openarchives.org/OAI/2.0/}header'). \
          find('{http://www.openarchives.org/OAI/2.0/}identifier').text.replace(
          'oai:pangaea.de:', '')
        record_date = record.find('{http://www.openarchives.org/OAI/2.0/}header'). \
          find('{http://www.openarchives.org/OAI/2.0/}datestamp').text
        # convert datetime as string to timezone aware datetime:
        record_date = pytz.utc.localize(datetime.datetime.strptime(record_date, '%Y-%m-%dT%H:%M:%SZ'))
        scimeta = ET.tostring(record.find('{http://www.openarchives.org/OAI/2.0/}metadata'). \
                              find(SCIMETA_ELEMENT))
        checkExistsDict = client_mgr.check_if_identifier_exists(identifier)

      except Exception as e:
        logging.error('Error processing an OAI-PMH result: {}'.format(e))

      # the outcome of checkExistsDict determines how to handle the record.
      # if identifier exists in GMN but record date is different, this truly is an update so call update method.
      if (checkExistsDict['outcome'] == 'yes' and checkExistsDict['record_date'] != record_date):
        if client_mgr.update_science_metadata(minidom.parseString(scimeta).toprettyxml(encoding='utf-8'),
                                              identifier, record_date, checkExistsDict['current_version_pid']):
          updated_count += 1  # track the number of succesfully updated objects
      # if identifier exists but record date is the same, it's not really an update. So skip it and move on.
      elif checkExistsDict['outcome'] == 'yes' and checkExistsDict['record_date'] == record_date:
        pass # identifier exists but there are no updates to apply because record date is the same
        skipped_exists_count += 1
      # if check failed for some reason, d1_client_manager would have logged the error so just skip.
      elif checkExistsDict['outcome'] == 'failed':
        pass
      # If this identifer is not already found in GMN in any way, then create a new object in GMN
      elif checkExistsDict['outcome'] == 'no':
        if client_mgr.load_science_metadata(minidom.parseString(scimeta).toprettyxml(encoding='utf-8'),
                                            identifier,
                                            record_date):
          created_count += 1  # track number of successfully created new objects

# ----------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
  main()
