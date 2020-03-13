"""
DATAONE adapter for IEDA

IEDA implements Schema.org, but not to our liking.   There is no top-level
encoding key, so the series ID and metadata URL have to be retrieved from other
locations in the JSON-LD.  The dateModified is only taken from the sitemap.

metadata URL:
    The url field in one of the distribution list items in the SO.
dateModified:
    Taken from the sitemap.
PID (record version):
    Given by the URL of the landing page.
SID (series ID):
    DOI given in the top-level '@id' key in the JSON-LD.
"""
# Standard library imports
import re

# Local imports

from .jsonld_validator import JsonLdError
from .so_core import SchemaDotOrgHarvester


class IEDAHarvester(SchemaDotOrgHarvester):

    def __init__(self, **kwargs):
        kwargs['sitemap_url'] = 'http://get.iedadata.org/sitemaps/usap_sitemap.xml'  # noqa : E501
        super().__init__(id='ieda', **kwargs)

        self.sys_meta_dict['authoritativeMN'] = 'urn:node:mnTestIEDA'
        self.sys_meta_dict['originMN'] = 'urn:node:mnTestIEDA'
        self.sys_meta_dict['rightsholder'] = 'CN=urn:node:mnTestIEDA,DC=dataone,DC=org'  # noqa : E501
        self.sys_meta_dict['submitter'] = 'CN=urn:node:mnTestIEDA,DC=dataone,DC=org'  # noqa : E501

    def generate_system_metadata(self, *,
                                 scimeta_bytes=None,
                                 native_identifier_sid=None,
                                 record_date=None,
                                 record_version=None):
        """
        This function generates a system metadata document for describing
        the science metadata record being loaded. Some of the fields,
        such as checksum and size, are based off the bytes of the science
        metadata object itself. Other system metadata fields are passed
        to D1ClientManager in a dict which is configured in the main
        adapter program.  Note that the checksum is assigned as an
        arbitrary version identifier to accommodate the source system's
        mutable content represented in the target system's immutable
        content standard.

        Parameters
        ----------
        scimeta_bytes :
            Bytes of the node's original metadata document.
        native_identifier_sid :
            Node's system identifier for this object, which becomes the series
            ID, or sid.
        record_date :
            Date metadata document was created/modified in the source
            system. Becomes dateUploaded.
        record_version : str
            Will be the pid.

        Returns
        -------
            A dict containing node-specific system metadata properties that
            will apply to all science metadata documents loaded into GMN.
        """
        kwargs = {
            'scimeta_bytes': scimeta_bytes,
            'native_identifier_sid': native_identifier_sid,
            'record_date': record_date,
            'record_version': record_version,
        }
        sys_meta = super().generate_system_metadata(**kwargs)

        sys_meta.identifier = record_version
        return sys_meta

    def extract_record_version(self, doc, landing_page_url):
        """
        Parameters
        ----------
        doc : ElementTree
            XML metadata document
        landing_page_url : str
            URL of the landing page

        Returns
        -------
        The record version for GMN.  In IEDA, it is the landing page URL.
        """
        return landing_page_url

    def extract_series_identifier(self, jsonld):
        """
        Parse the DOI from the json['@id'] value.  IEDA identifiers usually
        look something like

            'doi:10.15784/601015'

        The DOI in this case would be '10.15784/601015'.  This will be used as
        the series identifier.

        Parameters
        ----------
        JSON-LD obj

        Returns
        -------
        The identifier substring.
        """
        pattern = r'''
            # possible leading white space (not supposed to be there)
            \s*
            # DOI:prefix/suffix - IEDA style
            (((https?://dx.doi.org/)|(doi:))(?P<expected_doi>10\.\w+/\w+))
                |
            # other IEDA-style
            (?P<other_doi>urn:usap-dc:metadata:\w+)
            # possible trailing white space (not supposed to be there)
            \s*
        '''
        regex = re.compile(pattern, re.VERBOSE)
        m = regex.search(jsonld['@id'])
        if m is None:
            msg = (
                f"DOI ID parsing error, could not parse an ID out of "
                f"JSON-LD '@id' element \"{jsonld['@id']}\""
            )
            raise JsonLdError(msg)

        if m.group('expected_doi') is not None:
            return m.group('expected_doi')
        else:
            return m.group('other_doi')

    def extract_metadata_url(self, jsonld):
        """
        Extract the URL for the XML metadata document.

        For IEDA, the location is different.  We want to find it in 'encoding'
        ==> 'contentUrl', but instead it is in 'distribution' ==> 'url'

        Parameters
        ----------
        jsonld : dict
            Dictionary of JSON-LD data.

        Returns
        -------
        The URL for the XML metadata document.
        """
        urls = [
            dist['url'] for dist in jsonld['distribution']
            if dist['name'] == 'ISO Metadata Document'
        ]
        if len(urls) == 1:
            metadata_url = urls[0]
        else:
            msg = "Unable to determine a unique metadata URL from the JSON-LD."
            raise JsonLdError(msg)
        return metadata_url

