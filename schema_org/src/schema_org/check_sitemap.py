# Standard library imports

# 3rd party library imports

# local imports
from .core import CommonHarvester


class D1CheckSitemap(CommonHarvester):
    """
    Front end to validate a remote sitemap.
    """

    def __init__(self, sitemap_url=None, **kwargs):
        super().__init__(id='d1checksite', **kwargs)

        self.site_map = sitemap_url
        self.logger.debug(f'num_workers = {self.num_workers}')

    async def harvest_document(self, doi, doc, record_date):
        """
        We don't actually harvest.
        """
        pass

    def summarize(self):
        """
        We don't harvest, so summarization is much simpler.
        """
        msg = f'Successfully processed {self.num_records_processed} records.'
        self.logger.info(msg)
