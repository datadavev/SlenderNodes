"""
DATAONE Schema.Org core functionality.  This is meant to be subclassed by
individual adaptors for different Slendernodes.
"""

# Standard library imports
import json
import re
import urllib.parse

# 3rd party library imports
import lxml.etree

# Local imports
from .core import CoreHarvester, NO_JSON_LD_SCRIPT_ELEMENTS, SkipError
from .jsonld_validator import JSONLD_Validator, JsonLdError
from . import sotools


class SchemaDotOrgHarvester(CoreHarvester):
    """
    Harvester object with schema.org support.

    Attributes
    ----------
    jsonld_validator : obj
        Run conformance checks on the JSON-LD extracted from a site page.
    """

    def __init__(self, id='', **kwargs):
        super().__init__(id=id, **kwargs)

        self._jsonld_validator = JSONLD_Validator(id=id, logger=self.logger)

    def get_jsonld(self, doc):
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
        self.logger.debug('Retrieving JSON-LD from landing page...')
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

    def extract_series_identifier(self, sid):
        """
        Retrieve (or at least validate) the series identifier.

        Parameters
        ----------
        sid : str
            An identifier parsed from the JSON-LD.

        Returns
        -------
        the identifier
        """
        # Just make sure we can parse it as a URL.
        p = urllib.parse.urlparse(sid)
        if (
            'http' not in p.scheme 
            or len(p.netloc) == 0
            or len(p.path) == 0
        ):
            msg = (
                f"DOI ID parsing error, could not parse an ID out of "
                f"JSON-LD '@id' element \"sid\""
            )
            raise JsonLdError(msg)
        return sid

    async def retrieve_landing_page_content(self, landing_page_url):
        """
        Read the remote document.

        Parameters
        ----------
        landing_page_url : str
            URL for remote landing page HTML

        Returns
        -------
        doc : ElementTree
            ElementTree corresponding to the HTML in the landing page.
        """
        self.logger.info(f"Requesting landing page {landing_page_url}...")
        content, headers = await self.retrieve_url(landing_page_url)
        if 'text/html' not in headers['Content-Type']:
            msg = (
                f"Landing page was {headers['Content-Type']} "
                f"and not text/html."
            )
            raise RuntimeError(msg)
        doc = lxml.etree.HTML(content)
        return doc

    def validate_dataone_so_jsonld(self, jsonld):
        """
        Validate JSON-LD as conforming to our particular flavor of schema.org.
        Retrieve the JSON-LD from the landing page URL and validate it.
        """
        self._jsonld_validator.check(jsonld)

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
        last_modified : datetime or None
        doc : ElementTree
        """
        self.logger.info(f"Retrieving landing page {landing_page_url}")
        content, _ = await self.retrieve_url(landing_page_url)
        html = content.decode('utf-8')
        doc = lxml.etree.HTML(content)
        if doc is None:
            msg = "The landing page at {landing_page_url} has no content."
            raise RuntimeError(msg)

        # This section of code may be removable.
        jsonld = self.get_jsonld(doc)
        self.validate_dataone_so_jsonld(jsonld)

        g = sotools.common.loadSOGraphFromHtml(html, landing_page_url)

        # Try as ARM-style SO content first.
        mlinks = sotools.common.getDatasetMetadataLinks(g)
        if len(mlinks) == 0:
            # Try as BCO-DMO-style if necessary.
            mlinks = sotools.common.getDatasetMetadataLinksFromSubjectOf(g)
            if len(mlinks) == 0:
                msg = f"Unable to extract metadata links from {landing_page_url}."
                raise RuntimeError(msg)

        # extract the XML metadata URL
        metadata_url = mlinks[0]['contentUrl']

        # extract the series identifier
        subjectOf = mlinks[0]['subjectOf']

        sid = self.extract_series_identifier(subjectOf)
        self.logger.debug(f"Series ID (sid): {sid}")

        # extract the PID
        # This is currently None for ARM.  Will it be the case for all SO
        # documents?  Non-SO docs must provide custom code to get the PID.
        pid = None

        dateModified = sotools.common.getDateModified(g)

        self.logger.info(f"Retrieving XML metadata document {metadata_url}")
        doc = await self.retrieve_metadata_document(metadata_url)

        self.logger.debug(f"Record version (pid): {pid}")

        return sid, pid, dateModified, doc
