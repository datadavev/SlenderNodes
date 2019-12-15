"""
DATAONE Schema.Org core functionality.  This is meant to be subclassed by
individual adaptors for different Slendernodes.
"""

# Standard library imports
import json
import re

# 3rd party library imports
import lxml.etree

# Local imports
from .core import CoreHarvester, NO_JSON_LD_SCRIPT_ELEMENTS
from .jsonld_validator import JSONLD_Validator, JsonLdError


class SchemaDotOrgHarvester(CoreHarvester):
    """
    Harvester object with schema.org support.

    Attributes
    ----------
    jsonld_validator : obj
        Run conformance checks on the JSON-LD extracted from a site page.
    sitemap : str
        URL for XML site map.  This must be overridden for each custom client.
    """

    def __init__(self, id='', **kwargs):
        super().__init__(id=id, **kwargs)

        self.jsonld_validator = JSONLD_Validator(id=id, logger=self.logger)

        self.sitemap = ''

    def extract_jsonld(self, doc):
        """
        Extract JSON-LD from HTML document.

        Parameters
        ----------
        doc : ElementTree
            The parsed HTML.  The JSON-LD should be embedded within a
            <SCRIPT> element embedded in the <HEAD> element.

        Returns
        -------
        Dictionary of JSON-LD data.
        """
        self.logger.debug('extract_jsonld:')
        path = './/script[@type="application/ld+json"]'
        scripts = doc.xpath(path)
        if len(scripts) == 0:
            raise JsonLdError(NO_JSON_LD_SCRIPT_ELEMENTS)

        jsonld = None
        for script in scripts:

            j = json.loads(script.text)
            if '@type' in j and j['@type'] == 'Dataset':
                jsonld = j

        if jsonld is None:
            msg = (
                "Could not locate a JSON-LD <SCRIPT> element with @type "
                "\"Dataset\"."
            )
            raise JsonLdError(msg)

        return jsonld

    def extract_series_identifier(self, d):
        """
        Parse the DOI from the json['@id'] value.  The identifiers should
        look something like

            'https://dx.doi.org/10.5439/1025173

        The DOI in this case would be 'doi:10.5439/1025173'.  This will be used
        as the series identifier.

        Parameters
        ----------
        d : a valid python dictionary created from a JSON-LD string
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
        m = regex.search(d['@id'])
        if m is None:
            msg = (
                f"DOI ID parsing error, could not parse an ID out of "
                f"JSON-LD '@id' element \"{d['@id']}\""
            )
            raise JsonLdError(msg)

        identifier = f"doi:{m.group('doi')}"
        return identifier

    async def retrieve_record(self, landing_page_url):
        """
        Read the remote document, extract the JSON-LD, and load it into the
        system.

        Parameters
        ----------
        landing_page_url : str
            URL for remote landing page HTML

        Returns
        -------
        sid : str
            Node's system identifier for this object, which becomes the
            series ID.
        pid : str
            Intended to be the GMN unique identifier of the science
            metadata record to be archived.
        doc : ElementTree
        """
        self.logger.debug(f'retrieve_record')
        self.logger.info(f"Requesting {landing_page_url}...")
        content = await self.retrieve_url(landing_page_url)
        doc = lxml.etree.HTML(content)

        self.preprocess_landing_page(doc)

        jsonld = self.extract_jsonld(doc)
        self.jsonld_validator.check(jsonld)

        sid = self.extract_series_identifier(jsonld)
        self.logger.debug(f"Series ID (sid): {sid}")

        metadata_url = self.extract_metadata_url(jsonld)

        doc = await self.retrieve_metadata_document(metadata_url)

        pid = self.extract_record_version(doc, landing_page_url)
        self.logger.debug(f"Record version (pid): {pid}")

        return sid, pid, doc

    def extract_record_version(self, doc, landing_page_url):
        """
        Get the PID.  The default SO case is to set it to None.  This should
        eventually be turned into a checksum.

        Parameters
        ----------
        doc : ElementTree
            XML metadata document
        landing_page_url : str
            URL of the landing page

        Returns
        -------
        The record version for GMN.
        """
        return None

    def extract_metadata_url(self, jsonld):
        """
        Extract the URL for the XML metadata document.

        Parameters
        ----------
        jsonld : dict
            Dictionary of JSON-LD data.

        Returns
        -------
        The URL for the XML metadata document.
        """
        metadata_url = jsonld['encoding']['contentUrl']
        return metadata_url
