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
import re

# Local imports
from .so_core import SchemaDotOrgHarvester
from .jsonld_validator import JsonLdError


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

    def extract_series_identifier(self, sid):
        """
        Parse the DOI from the JSON-LD ['@id'] value.  The identifiers for ARM
        look something like

            'https://dx.doi.org/10.5439/1025173

        The DOI in this case would be 'doi:10.5439/1025173'.  This will be used
        as the series identifier.

        Parameters
        ----------
        sid : str
            This has hopefully been extracted from a JSON-LD <SCRIPT> element
            from a landing page.

        Returns
        -------
        the DOI identifier
        """
        pattern = r'''
                  # DOI:prefix/suffix - ARM style
                  (https?://dx.doi.org/(?P<doi>10\.\w+/\w+))
                  '''
        regex = re.compile(pattern, re.VERBOSE)
        m = regex.search(sid)
        if m is None:
            msg = (
                f"DOI ID parsing error, could not parse an ID out of "
                f"JSON-LD '@id' element \"sid\""
            )
            raise JsonLdError(msg)

        identifier = f"doi:{m.group('doi')}"
        return identifier

