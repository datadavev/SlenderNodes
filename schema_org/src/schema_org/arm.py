"""
DATAONE adapter for ARM
=======

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

    def __init__(self, **kwargs):
        super().__init__(id='arm', **kwargs)

        self.sitemap = 'https://www.archive.arm.gov/metadata/adc/sitemap.xml'  # noqa: E501

        self.sys_meta_dict['authoritativeMN'] = 'urn:node:mnTestARM'
        self.sys_meta_dict['originMN'] = 'urn:node:mnTestARM'
        self.sys_meta_dict['rightsholder'] = 'CN=urn:node:mnTestARM,DC=dataone,DC=org'  # noqa : E501
        self.sys_meta_dict['submitter'] = 'CN=urn:node:mnTestARM,DC=dataone,DC=org'  # noqa : E501
