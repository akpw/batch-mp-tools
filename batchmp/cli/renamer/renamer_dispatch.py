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

from batchmp.cli.base.bmp_dispatch import BatchMPDispatcher
from batchmp.cli.renamer.renamer_options import RenameArgParser, RenamerCommands
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.rename import Renamer
from batchmp.fstools.builders.fsprms import FSEntryParamsBase, FSEntryParamsExt, FSEntryParamsFlatten
from batchmp.fstools.builders.fsb import FSEntryBuilderBase

class RenameDispatcher(BatchMPDispatcher):
    ''' Renamer Commands Dispatcher
    '''
    def __init__(self):
        self.option_parser = RenameArgParser()

    # Dispatcher
    def dispatch(self):
        ''' Dispatches Renamer commands
        '''
        if not super().dispatch():
            args = self.option_parser.parse_options()
            if args['sub_cmd'] == RenamerCommands.PRINT:
                self.print_dir(args)

            elif args['sub_cmd'] == RenamerCommands.FLATTEN:
                self.flatten(args)

            elif args['sub_cmd'] == RenamerCommands.INDEX:
                self.add_index(args)

            elif args['sub_cmd'] == RenamerCommands.ADD_DATE:
                self.add_date(args)

            elif args['sub_cmd'] == RenamerCommands.ADD_TEXT:
                self.add_text(args)

            elif args['sub_cmd'] == RenamerCommands.REMOVE:
                self.remove(args)

            elif args['sub_cmd'] == RenamerCommands.REPLACE:
                self.replace(args)

            elif args['sub_cmd'] == RenamerCommands.CAPITALIZE:
                self.capitalize(args)

            elif args['sub_cmd'] == RenamerCommands.DELETE:
                self.delete(args)

            elif args['sub_cmd'] == RenamerCommands.STATS:
                self.stats(args)

            else:
                print('Nothing to dispatch')
                return False

        return True

    # Dispatched Methods
    def print_dir(self, args):
        fs_entry_params = FSEntryParamsBase(args)
        DHandler.print_dir(fs_entry_params)

    def stats(self, args):
        fs_entry_params = FSEntryParamsBase(args)
        DHandler.stats(fs_entry_params)

    def flatten(self, args):
        fs_entry_params = FSEntryParamsFlatten(args)
        DHandler.flatten_folders(fs_entry_params)

    def add_index(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        Renamer.add_index(fs_entry_params, 
                as_prefix = not args['as_suffix'], join_str = args['join_str'],
                start_from = args['start_from'], min_digits = args['min_digits'],
                sequential = args['sequential'], by_directory = args['by_directory'])

    def add_date(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        Renamer.add_date(fs_entry_params, 
                as_prefix = args['as_prefix'], join_str = args['join_str'], format = args['format'])

    def add_text(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        Renamer.add_text(fs_entry_params,
                text = args['text'], as_prefix = args['as_prefix'], join_str = args['join_str'])

    def remove(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        Renamer.remove_n_characters(fs_entry_params, num_chars = args['num_chars'], from_head = not args['from_tail'])

    def replace(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        Renamer.replace(fs_entry_params, 
                find_str = args['find_str'],
                replace_str = args['replace_str'] if 'replace_str' in args else None,
                case_insensitive = args['ignore_case'],
                include_extension = args['include_extension'])

    def capitalize(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        Renamer.capitalize(fs_entry_params)

    def delete(self, args):
        fs_entry_params = FSEntryParamsExt(args)
        Renamer.delete(fs_entry_params)


def main():
    ''' Renamer entry point
    '''
    RenameDispatcher().dispatch()
