"""
DATAONE adapter for Arctic Biodiversity Data Service, IPT (Integrated
Publishing Toolkit).

See http://geo.abds.is/ipt/

ABDS IPT does not implement Schema.org, but instead does something similar,
making available an RSS feed.  An individual record from the RSS feed looks
something like.

      <item>
        <title>
            Phytoplankton from the White Sea,
            Barents Sea, Norwegian Sea and Arctic Basin 1993-2003
            - Version 1.3
        </title>
        <link>http://geo.abds.is/ipt/resource?r=arcod_2007p6</link>

        <!-- shows what changed in this version, or shows the resource
             description if change summary was empty -->
        <description>Correct scientificNameID</description>
        <author>hoddi@caff.is (Hólmgrímur Helgason)</author>
        <ipt:eml>http://geo.abds.is/ipt/eml.do?r=arcod_2007p6</ipt:eml>
        <ipt:dwca>http://geo.abds.is/ipt/archive.do?r=arcod_2007p6</ipt:dwca>
        <pubDate>Wed, 04 Sep 2019 10:54:41 +0000</pubDate>
        <guid isPermaLink="false">
            59876921-fda6-4fd5-af5d-cba2a7152527/v1.3
        </guid>
      </item>

metadata URL:
    Given by the <ipt:eml> element in the RSS feed.
lastModified:
    Given by the <pubDate> element in the RSS feed.
PID (record version):
    This is available both in the <guid> element in the RSS feed and in the
    packageVersion attribute in the top level element in the metadata document.
SID (series ID):
    The series ID is extracted from the metadata document.  It could likely
    be inferred from the PID, however.
"""

# Standard library imports
import io

# 3rd party library imports
import dateutil.parser
import lxml.etree

# Local imports
from .core import CoreHarvester

# Namespaces used in the ABDS RSS feed.
SITEMAP_NS = {
    'ipt': 'http://ipt.gbif.org/',
    'atom': 'http://www.w3.org/2005/Atom',
    'geo':  'http://www.w3.org/2003/01/geo/wgs84_pos#'
}

EML_211_NSMAP = {
    'eml': 'eml://ecoinformatics.org/eml-2.1.1',
    'dc': 'http://purl.org/dc/terms/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}


class AbdsIptHarvester(CoreHarvester):

    def __init__(self, **kwargs):
        super().__init__(id='abds_ipt', **kwargs)

        self.sitemap = 'http://geo.abds.is/ipt/rss.do'

        self.sys_meta_dict['authoritativeMN'] = 'urn:node:mnTestABDS'
        self.sys_meta_dict['originMN'] = 'urn:node:mnTestABDS'
        self.sys_meta_dict['rightsholder'] = 'CN=urn:node:mnTestABDS,DC=dataone,DC=org'  # noqa : E501
        self.sys_meta_dict['submitter'] = 'CN=urn:node:mnTestABDS,DC=dataone,DC=org'  # noqa : E501

    def is_sitemap_index_file(self, doc):
        """
        Answer the question as to whether the document found at the other end
        of the sitemap URL is a sitemap index file - i.e. it references other
        sitemaps - or if it is a sitemap leaf.

        In the case of an RSS fead, no, it is not and index file, it is its own
        leaf.
        """
        return False

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

    def extract_records_from_sitemap(self, doc):
        """
        Extract all the URLs and lastmod times from the RSS feed.

        Parameters
        ----------
        doc : ElementTree
            XML document constructed out of RSS feed

        Returns
        -------
        List of records (URLs of metadata documents and publishing dates).
        """
        path = 'channel/item/ipt:eml/text()'
        urls = doc.xpath(path, namespaces=SITEMAP_NS)

        path = 'channel/item/pubDate/text()'
        lastmods = doc.xpath(path, namespaces=SITEMAP_NS)
        lastmods = [dateutil.parser.parse(item) for item in lastmods]

        records = [(url, lastmod) for url, lastmod in zip(urls, lastmods)]

        msg = f"Extracted {len(urls)} from the sitemap document."
        self.logger.info(msg)

        return records

    async def retrieve_record(self, metadata_url):
        """
        Retrieve the metadata record

        Parameters
        ----------
        metadata_url : str
            URL for remote XML metadata file

        Returns
        -------
        sid : str
            Ideally this is a DOI, but here it is a UUID.
        pid : str
            The version of the document.
        doc : ElementTree
            Metadata document
        """
        self.logger.debug(f'retrieve_record')
        self.logger.info(f"Requesting {metadata_url}...")
        content = await self.retrieve_url(metadata_url)
        doc = lxml.etree.parse(io.BytesIO(content))

        # Normally it would make sense to factor this out, but the schema.org,
        # it gets a lot more complicated.
        sid = self.extract_series_identifier(doc)
        self.logger.debug(f"Have extracted the identifier {sid}...")

        pid = doc.getroot().attrib['packageId']
        self.logger.debug(f"Have extracted the version ID {pid}...")

        return sid, pid, doc

    def extract_series_identifier(self, doc):
        """
        Parse the identifier from the XML.

        Parameters
        ----------
        XML document

        Returns
        -------
        Ideally this is a DOI, but here it is a UUID.
        """
        path = '/eml:eml/dataset/alternateIdentifier[1]/text()'
        elts = doc.xpath(path, namespaces=EML_211_NSMAP)
        identifier = elts[0]
        return identifier
