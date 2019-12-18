"""
DATAONE adapter for CUAHSI

Hydroshare/CUAHSI has nested sitemaps and partially implements Schema.Org.  The
SO implementation is not fully to our liking, however.  Neither is the sitemap
implementation, as it has no lastmod entries.

metadata URL:
    This is indirect.  The landing page provides a URL for downloading a "bagit
    zip archive" that contains the metadata along with the data itself.
lastModified:
    Taken from the sitemap.
PID (record version):
    MD5 digest of the zip archive content
SID (series ID):
    DOI taken from the '@id' key in the SO.
"""

# Standard library imports
import importlib.resources as ir
import hashlib
import io
import json
import zipfile

# 3rd party library imports
import lxml.etree

# Local imports
from .so_core import SchemaDotOrgHarvester, NO_JSON_LD_SCRIPT_ELEMENTS
from .core import SkipError, XMLMetadataParsingError


class CUAHSIHarvester(SchemaDotOrgHarvester):

    def __init__(self, **kwargs):
        kwargs['sitemap_url'] = 'https://www.hydroshare.org/sitemap.xml'
        super().__init__(id='cuahsi', **kwargs)

        # Create an XSLT stylesheet for transforming the CUAHSI documents
        # from their native format to something we can use (simplified DC).
        content = ir.read_binary('schema_org.data', 'simple_d1_dublincore.xsl')
        xslt_tree = lxml.etree.XML(content)
        self.transform_to_dataone_simple_dc = lxml.etree.XSLT(xslt_tree)

        self.sys_meta_dict['authoritativeMN'] = 'urn:node:mnTestHydroshare'
        self.sys_meta_dict['originMN'] = 'urn:node:mnTestHydroshare'
        self.sys_meta_dict['rightsholder'] = 'CN=urn:node:mnTestHydroshare,DC=dataone,DC=org'  # noqa : E501
        self.sys_meta_dict['submitter'] = 'CN=urn:node:mnTestHydroshare,DC=dataone,DC=org'  # noqa : E501

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
        doc = await super().retrieve_landing_page_content(landing_page_url)
        self.preprocess_landing_page(doc)
        return doc

    def preprocess_landing_page(self, landing_page_doc):
        """
        Check the landing page for any information we may need OTHER than
        JSON-LD.

        Parameters
        ----------
        landing_page_doc : lxml element tree
            Document corresponding to the HTML landing page.
        """

        # We require the presense of a hl-sharing-status element.
        path = './/td[@id="hl-sharing-status"]/text()'
        elts = landing_page_doc.xpath(path)
        if len(elts) == 0:
            msg = "No sharing status element found."
            self.logger.debug(msg)
            raise SkipError(msg)

        sharing_status = elts[0].strip().upper()

        # That hl-sharing-status element must be PUBLISHED.  It it is not, then
        # we want to skip this document.
        self.logger.debug(f"Sharing status is {sharing_status}.")
        if sharing_status != 'PUBLISHED':
            msg = (
                f"CUAHSI landing page sharing status is {sharing_status} "
                f"instead of PUBLISHED."
            )
            raise SkipError(msg)

    def extract_jsonld(self, doc):
        """
        Extract JSON-LD from HTML document.

        Parameters
        ----------
        doc : ElementTree
            The parsed HTML.  The JSON-LD should be embedded within a
            <SCRIPT> element embedded in the <HEAD> element.
        """
        self.logger.debug('extract_jsonld:')
        path = './/script[@type="application/ld+json"]'
        scripts = doc.xpath(path)
        if len(scripts) == 0:
            raise SkipError(NO_JSON_LD_SCRIPT_ELEMENTS)

        jsonld = json.loads(scripts[0].text)
        return jsonld

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
            Ideally this is a DOI, but here it is a UUID.
        pid : None
            There is no record version available.
        lastMod : None
            Rely on the RSS feed for this.
        doc : ElementTree
            Metadata document
        """
        self.logger.debug(f'retrieve_record')
        self.logger.info(f"Requesting {landing_page_url}...")
        content, _ = await self.retrieve_url(landing_page_url)
        self.logger.debug(f'got the landing page')
        doc = lxml.etree.HTML(content)
        self.logger.debug(f'got the doc')

        self.preprocess_landing_page(doc)
        self.logger.debug(f'pre-processed the landing page')

        jsonld = self.extract_jsonld(doc)
        self.logger.debug(f'got the JSON-LD')

        # Don't bother validating, we know it fails.
        # self.jsonld_validator.check(jsonld)

        sid = self.extract_series_identifier(jsonld)
        self.logger.debug(f"Have extracted the identifier {sid}...")

        # Construct the URL for the bagit zip archive.
        path = './/a[@id="btn-download-all"]'
        elt = doc.xpath(path)[0]
        if 'href' not in elt.attrib:
            msg = (
                f"The landing page at {landing_page_url} likely has a dialog "
                f"pop-up that is fouling our attempts to download the zip "
                f"archive.  This needs to be addressed."
            )
            raise SkipError(msg)

        url = 'https://www.hydroshare.org/' + elt.attrib['href']

        doc, pid = await self.retrieve_metadata_document(url)

        # Must transform the document.
        doc = self.transform_to_dataone_simple_dc(doc)

        return sid, pid, None, doc

    def extract_series_identifier(self, jsonld):
        """
        Parse the DOI from the json['@id'] value.  The identifiers should
        look something like

            'https://dx.doi.org/10.5439/1025173

        The DOI in this case would be '10.5439/1025173'.  This will be used as
        the series identifier.

        Parameters
        ----------
        JSON-LD obj

        Returns
        -------
        The identifier substring.
        """
        identifier = jsonld['identifier']['value']
        return identifier

    async def retrieve_metadata_document(self, url):
        """
        Retrieve the remote metadata document and make any necessary
        transformations on it.

        Parameters
        ----------
        url : str
            URL of remote bagit zip archive

        Returns
        -------
        doc : ElementTree
            The XML metadata document
        pid : str
            Record version.  For CUAHSI, it is the checksum of the zip file.
        """

        self.logger.debug(f'Requesting bagit zip archive: {url}')

        # Retrieve the metadata document.
        zip_content, _ = await self.retrieve_url(url)
        self.logger.debug(f'zip archive length: {len(zip_content)}')

        b = io.BytesIO(zip_content)
        zf = zipfile.ZipFile(b)

        for name in zf.namelist():
            if 'resourcemetadata' in name:
                with zf.open(name, mode='r') as f:
                    content = f.read()

        try:
            doc = lxml.etree.parse(io.BytesIO(content))
        except Exception as e:
            msg = f"Unable to parse the metadata document at {url}:  {e}."
            raise XMLMetadataParsingError(msg)
        else:
            self.logger.debug('Got the metadata document')

        pid = hashlib.md5(zip_content).hexdigest()
        msg = (
            f"Got the pid {pid} as an MD5 hexdigest from the zip archive "
            f"content."
        )
        self.logger.debug(msg)

        return doc, pid
