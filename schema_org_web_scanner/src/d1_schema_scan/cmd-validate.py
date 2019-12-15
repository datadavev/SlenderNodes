#!/usr/bin/env python

import sys
import xml_validator

import d1_cmd.cmd_log
import logging

# import d1_common.util.process


def main():
    log = d1_cmd.cmd_log.getLogger(__name__)
    log.setLevel(log.DEBUG)

    # d1_cmd.cmd_log.setup(is_debug=True)
    d1_cmd.cmd_log.setup(is_debug=False)

    logging.getLogger('d1_common.utils.process').disabled = True

    format_id = sys.argv[1]
    uri = sys.argv[2]

    # log.info(f'Validating: {uri}')
    # log.info(f'DataONE FormatId: {format_id}')

    validator = xml_validator.XMLValidator(verbosity='DEBUG')
    validator.validate(uri, format_id=format_id)


if __name__ == '__main__':
    main()
