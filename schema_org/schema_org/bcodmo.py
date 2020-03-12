"""
DATAONE adapter for BCO-DMO

metadata URL:
    Taken from contentUrl item in the top-level encoding map of the SO.
lastModified:
    Taken from the sitemap, but also available in the SO in the dateModified
    element of the top-level encoding map.
PID (record version):
    Given by the URL of the landing page.
SID (series ID):
    DOI taken from the '@id' key in the SO.
"""

# Standard library imports

# Local imports
from .core import ISO_NSMAP
from .so_core import SchemaDotOrgHarvester


class BCODMOHarvester(SchemaDotOrgHarvester):

    def __init__(self, host='localhost', port=443, **kwargs):
        sitemap_url = 'https://www.bco-dmo.org/sitemap.xml'
        kwargs['sitemap_url'] = sitemap_url

        super().__init__(id='bco-dmo', host=host, port=port,
                         base_path='/bcodmo', **kwargs)

        authoritative_mn = 'urn:node:mnTestBCODMO'
        self.sys_meta_dict['authoritativeMN'] = authoritative_mn
        self.sys_meta_dict['originMN'] = authoritative_mn

        rightsholder = 'CN=urn:node:mnTestBCODMO,DC=dataone,DC=org'
        self.sys_meta_dict['rightsholder'] = rightsholder
        self.sys_meta_dict['submitter'] = rightsholder

    def post_process_sitemap_records(self, records, last_harvest_time):
        """
        Prune the sitemap records for various reasons.  In addition to the
        superclass reasons, we also prune any URL that does not contain the
        string "dataset".

        Parameters
        ----------
        records : list
            Each item in the list is composed of a URL and a last modification
            date.
        last_harvest_time : datetime
            datetime of last harvest
        """
        # If we do not wish to ignore the last harvest time, then only those
        # records in the sitemap that are newer than the last harvest time will
        # pass through.
        records = super().post_process_sitemap_records(records,
                                                       last_harvest_time)
        nrecs = len(records)

        records = [
            (url, lastmod) for url, lastmod in records
            if 'dataset' in url
        ]

        num_skipped = nrecs - len(records)
        msg = (
            f"{num_skipped} records skipped due to dataset-in-URL restriction."
        )
        self.logger.info(msg)

        return records
