#!/usr/bin/env python
# coding=utf8
## Copyright (c) 2014 Arseniy Kuznetsov
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

import pkg_resources
import batchmp.cli.base.vchk
from batchmp.cli.base.bmp_options import BatchMPArgParser, BatchMPBaseCommands


class BatchMPDispatcher:
    ''' Base BatchMP Commands Dispatcher
    '''
    def __init__(self):
        self.option_parser = BatchMPArgParser()

    # Dispatcher
    def dispatch(self):
        args = self.option_parser.parse_options()

        if args['sub_cmd'] == BatchMPBaseCommands.VERSION:
            self.print_version()

        elif args['sub_cmd'] == BatchMPBaseCommands.INFO:
            self.print_info()

        else:
            # nothing to dispatch
            return False

        return True

    # Dispatched methods
    def print_version(self):
        ''' Prints BatchMP version info
        '''
        version = pkg_resources.require("batchmp")[0].version
        print('BatchMP tools version {}'.format(version))

    def print_info(self):
        print('\nBatch Media Processing Tools: {}'.format(self.option_parser.script_name))
        print(self.option_parser.description)

def main():
    ''' BatchMP entry point
    '''
    BatchMPDispatcher().dispatch()

if __name__ == '__main__':
    main()

