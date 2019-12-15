"""
Check a sitemap as to availability and validity of metadata documents.  This
is for Schema.Org sites only.
"""

# Standard library imports

# 3rd party library imports
import dateutil.parser

# local imports
from .so_core import SchemaDotOrgHarvester


class D1CheckSitemap(SchemaDotOrgHarvester):
    """
    Front end to validate a remote sitemap.
    """

    def __init__(self, sitemap_url=None, **kwargs):
        super().__init__(id='d1checksite', **kwargs)

        self.sitemap = sitemap_url

    async def harvest_document(self, sid, pid, doc, record_date):
        """
        We don't actually harvest when just checking the sitemap, so do nothing
        here.
        """
        pass

    def summarize(self):
        """
        Summarize the harvest results.
        """

        self.logger.info("\n\n")
        self.logger.info("Job Summary")
        self.logger.info("===========")

        self.summarize_job_records()

    def get_last_harvest_time(self):
        """
        Get the last time that a harvest was run on this node.

        For the purposes of checking a sitemap, we really don't need this
        functionality.  Just give a date that is ridiculously distant in the
        past.

        Returns
        -------
        datetime of last harvest
        """

        last_harvest_time = dateutil.parser.parse('1900-01-01T00:00:00Z')
        return last_harvest_time
