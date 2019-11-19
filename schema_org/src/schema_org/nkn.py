"""
DATAONE adapter for NKN

NKN does not implement either Schema.org or sitemaps.  It also technically has
no landing pages, although they can technically be created from raw HTML
directory listings.

metadata URL:
    The metadata documents seem to always be "metadata.xml" relative URLs
    hanging off the parent directory listing URL.
dateModified:
    Taken from the raw HTML directory listing.
PID (record version):
    MD5 message digest of the bytes constituting the metadata document.
SID (series ID):
    A UUID parsed from the gmd:fileIdentifier element in the metadata document.
"""

# Standard library imports
import io

# 3rd party library imports
import aiohttp
import lxml.etree

# Local imports
from .core import CoreHarvester, ISO_NSMAP, SkipError


class MissingMetadataFileIdentifierError(RuntimeError):
    """
    Raise this exception if the GMD metadata file has an empty fileIdentifier
    element.
    """
    pass


class NKNHarvester(CoreHarvester):
    """
    NKN doesn't use Schema.Org or sitemaps, but raw HTML layout is similar to
    a sitemap.
    """
    SITEMAP_URL_PATH = (
        "xhtml:body"
        "/xhtml:table"
        "/xhtml:tr"
        "/xhtml:td"
        "/xhtml:a[@href]/text()"
    )
    SITEMAP_LASTMOD_PATH = (
        "xhtml:body"
        "/xhtml:table"
        "/xhtml:tr"
        "/xhtml:td[@class='indexcollastmod']/text()"
    )
    SITEMAP_NAMESPACE = {'xhtml': 'http://www.w3.org/1999/xhtml'}

    def __init__(self, **kwargs):
        super().__init__(id='core', **kwargs)

        self.sitemap = 'https://www.northwestknowledge.net/data/'

        self.sys_meta_dict['authoritativeMN'] = 'urn:node:mnTestNKN'
        self.sys_meta_dict['originMN'] = 'urn:node:mnTestNKN'
        self.sys_meta_dict['rightsholder'] = 'CN=urn:node:mnTestNKN,DC=dataone,DC=org'  # noqa : E501
        self.sys_meta_dict['submitter'] = 'CN=urn:node:mnTestNKN,DC=dataone,DC=org'  # noqa : E501

    def extract_series_identifier(self, doc):
        """
        Parse the identifier from the XML metadata document.

        Parameters
        ----------
        doc : ElementTree
            metadata document

        Returns
        -------
        The identifier substring.  It should look something like
        "nkn:0a42d2bc-700a-4cf2-a7ac-ad6b892da7f0".  Just return the UUID
        portion of it.
        """
        path = './/gmd:fileIdentifier/gco:CharacterString/text()'
        elts = doc.xpath(path, namespaces=ISO_NSMAP)
        if len(elts) == 0:
            msg = "Missing a gmd:fileIdentifier element."
            raise MissingMetadataFileIdentifierError(msg)

        return elts[0].split(':')[1]

    def check_xml_headers(self, response):
        """
        Check the headers returned by the sitemap request response.

        In the case of NKN, do nothing, we already know it is not XML.

        Parameters
        ----------
        response : aiohttp.ClientResponse
            Response for the sitemap (just an HTML directory listing)
        """
        return

    async def retrieve_record(self, landing_page_url):
        """
        Retrieve the metadata record

        Parameters
        ----------
        landing_page_url : str
            URL for remote landing page URL, which in the case of NKN is just
            a raw HTML directory listing

        Returns
        -------
        sid : str
            Ideally this is a DOI, but here it is a UUID.
        pid : None
            There is no record version available.
        doc : ElementTree
            Metadata document
        """
        self.logger.debug(f'retrieve_record')
        self.logger.info(f"Requesting {landing_page_url}...")
        content = await self.retrieve_url(landing_page_url)
        lxml.etree.HTML(content.decode('utf-8'))

        # Get the metadata document.  Right now the relative URL is just
        # "metadata.xml".
        url = f"{landing_page_url}/metadata.xml"
        try:
            content = await self.retrieve_url(url)
        except aiohttp.ClientResponseError as e:
            if '404' in str(e):
                msg = f"No metadata.xml document found in {landing_page_url}"
                raise SkipError(msg)
            else:
                raise

        doc = lxml.etree.parse(io.BytesIO(content))

        # We have to deviate from the normal course of processing and validate
        # the document early.  Normally that would happen AFTER this routine
        # finished.
        self.validate_document(doc)

        # Normally it would make sense to factor this out, but the schema.org,
        # it gets a lot more complicated.
        sid = self.extract_series_identifier(doc)
        self.logger.debug(f"Have extracted the series ID {sid}...")

        return sid, None, doc
