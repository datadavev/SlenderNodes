#!/usr/bin/env python

import sys
import asyncio
import xml_validator
import testtool
import io
import traceback

import d1_cmd.cmd_log
import logging


def main():
    # sys.stdout = SourceLocTagger(sys.stdout)
    # sys.stderr = SourceLocTagger(sys.stderr)

    # d1_cmd.cmd_log.setup(is_debug=True)
    d1_cmd.cmd_log.setup(is_debug=False, disable_existing_loggers=True)

    log = d1_cmd.cmd_log.getLogger(__name__)
    log.setLevel(log.INFO)

    logging.getLogger('d1_scimeta.validate_xerces').disabled = True
    logging.getLogger('d1_common.utils.process').disabled = True

    uri = sys.argv[1]

    # print(f'Scanning sitemap: {uri}')

    obj = testtool.D1TestToolAsync(
        sitemap_url=uri, verbosity='INFO', num_workers=10, num_documents=1000
    )
    asyncio.run(obj.run())


class SourceLocTagger(io.TextIOBase):
    """Wrap an output stream and add source code locations to write()."""

    def __init__(self, stream, ending='\n'):
        self._stream = stream
        self.ending = ending

    def __getattr__(self, name):
        return getattr(self._stream, name)

    def isatty(self):
        return hasattr(self._stream, 'isatty') and self._stream.isatty()

    def fileno(self):
        return self._stream.fileno()

    def write(self, *args, **kw):
        traceback.print_stack()
        self._stream.write('-- ')
        self._stream.write(*args, **kw)


if __name__ == '__main__':
    main()
