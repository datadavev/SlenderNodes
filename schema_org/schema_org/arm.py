"""
DATAONE adapter for ARM

ARM does Schema.org right!

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
from .so_core import SchemaDotOrgHarvester


class ARMHarvester(SchemaDotOrgHarvester):

    def __init__(self, host='localhost', port=443, **kwargs):
        sitemap_url = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'
        kwargs['sitemap_url'] = sitemap_url

        super().__init__(id='arm', host=host, port=port, base_path='/arm',
                         **kwargs)

        authoritative_mn = 'urn:node:mnTestARM'
        self.sys_meta_dict['authoritativeMN'] = authoritative_mn
        self.sys_meta_dict['originMN'] = authoritative_mn

        rightsholder = 'CN=urn:node:mnTestARM,DC=dataone,DC=org'
        self.sys_meta_dict['rightsholder'] = rightsholder
        self.sys_meta_dict['submitter'] = rightsholder
