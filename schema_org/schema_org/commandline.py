# Standard library imports
import argparse
import asyncio

# 3rd party library imports
import d1_scimeta.util

# Local imports
from .abds import AbdsIptHarvester
from .arm import ARMHarvester
from .cuahsi import CUAHSIHarvester
from .ieda import IEDAHarvester
from .nkn import NKNHarvester
from .check_sitemap import D1CheckSitemap
from .xml_validator import XMLValidator


def setup_common_parser(id, description=None, epilog=None):
    """
    All the harvesters and utilities use a common parser.

    Parameters
    ----------
    id : str
        Name of the harvester, i.e. "arm" or "ieda".
    epilog : str
        Additional description for the utility.
    """

    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    help = f"Verbosity level of log file {id}.log"
    choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    parser.add_argument('-v', '--verbosity', choices=choices, default='INFO',
                        help=help)

    help = "Limit number of documents retrieved to this number."
    parser.add_argument('--num-documents', type=int, default=-1, help=help)

    help = (
        "Limit documents retrieved to those whose URL match this regular "
        "expression."
    )
    parser.add_argument('--regex', help=help)

    help = "Limit number of workers operating asynchronously to this number."
    parser.add_argument('--num-workers', type=int, default=1, help=help)

    help = (
        "Limit number of errors to this number.  This number is not exact, "
        "because if the number of asynchronous workers is more than one, it "
        "is possible that the threshold is passed simultaneously by more than "
        "one worker."
    )
    parser.add_argument('--max-num-errors', type=int, default=1, help=help)

    return parser


def add_harvesting_options(parser, id):
    """
    These are options that only make sense for actual harvesters, such as ARM.
    They do not make sense for utilities that do not perform harvesting, such
    as the sitemap checker.
    """

    help = (
        "Ignore the last harvest time.  Use this switch to attempt to "
        "harvest records that may have failed for some reason on a recent "
        "harvest attempt.  The regex option may also be useful here."
    )
    parser.add_argument('--ignore-harvest-time', action='store_true',
                        help=help)

    help = (
        "Retrieve and process all records, but do not attempt to harvest "
        "the records to GMN."
    )
    parser.add_argument('--no-harvest', action='store_true',
                        help=help)

    help = "Retry a failed record this number of times."
    parser.add_argument('--retry', type=int, default=1, help=help)

    help = "Harvest records to this DataOne member node."
    parser.add_argument('--host', default='localhost', help=help)

    help = "DataOne member node SSL port."
    parser.add_argument('--port', default=443, type=int, help=help)

    help = 'Path to dataone client-side certificate.'
    parser.add_argument('--certificate', default=None, help=help)

    help = 'Path to dataone host client-side key.'
    parser.add_argument('--private-key', default=None, help=help)

    parser.description = f"Harvest metadata from {id.upper()}."
    parser.epilog = (
        "Not supplying an argument to both the certificate and key arguments "
        "will disable client side authentication."
    )


def d1_check_site():

    id = 'site-checker'
    description = "Crawl a sitemap, check metadata for validity."
    parser = setup_common_parser(id, description=description)

    help = "URL of site map"
    parser.add_argument('sitemap_url', type=str, help=help)

    args = parser.parse_args()

    obj = D1CheckSitemap(**args.__dict__)
    asyncio.run(obj.run())


def abds_ipt():

    id = "abds_ipt"
    parser = setup_common_parser(id)
    add_harvesting_options(parser, id)

    args = parser.parse_args()

    harvester = AbdsIptHarvester(**args.__dict__)
    asyncio.run(harvester.run())


def arm():

    id = "arm"
    parser = setup_common_parser(id)
    add_harvesting_options(parser, id)

    args = parser.parse_args()

    harvester = ARMHarvester(**args.__dict__)
    asyncio.run(harvester.run())


def cuahsi():

    id = "cuahsi"
    parser = setup_common_parser(id)
    add_harvesting_options(parser, id)

    args = parser.parse_args()

    harvester = CUAHSIHarvester(**args.__dict__)
    asyncio.run(harvester.run())


def ieda():

    id = "ieda"
    parser = setup_common_parser(id)
    add_harvesting_options(parser, id)

    args = parser.parse_args()

    harvester = IEDAHarvester(**args.__dict__)
    asyncio.run(harvester.run())


def nkn():

    id = "nkn"
    parser = setup_common_parser(id)
    add_harvesting_options(parser, id)

    args = parser.parse_args()

    harvester = NKNHarvester(**args.__dict__)
    asyncio.run(harvester.run())


def validate():
    """
    Validate an XML document.
    """
    description = f"Validate XML metadata."
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    help = "XML file or URL"
    parser.add_argument('infile', help=help)

    help = (
        "Format ID for metadata standard.  If this argument is supplied, "
        "only that format ID will be checked.  If not, all format IDs will be "
        "checked."
    )
    parser.add_argument('--format-id',
                        help=help,
                        choices=d1_scimeta.util.get_supported_format_id_list())

    help = "Verbosity of log messages."
    choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    parser.add_argument('-v', '--verbosity', help=help, choices=choices,
                        default='INFO')

    args = parser.parse_args()

    validator = XMLValidator(verbosity=args.verbosity)
    validator.validate(args.infile, format_id=args.format_id)
