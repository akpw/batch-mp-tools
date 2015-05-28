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

            else:
                print('Nothing to dispatch')
                return False

        return True

    # Dispatched Methods
    def print_dir(self, args):
        DHandler.print_dir(src_dir = args['dir'],
                start_level = args['start_level'], end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                show_size = args['show_size'])

    def flatten(self, args):
            remove_folders = True if args['discard_flattened'] in ('de', 'da') else False
            remove_all_folders = True if args['discard_flattened'] == 'da' else False

            DHandler.flatten_folders(src_dir = args['dir'],
                end_level = args['end_level'],
                target_level = args['target_level'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                remove_folders = remove_folders, remove_non_empty_folders = remove_all_folders,
                display_current = args['display_current'], quiet = args['quiet'])

    def add_index(self, args):
        Renamer.add_index(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                as_prefix = not args['as_suffix'], join_str = args['join_str'],
                start_from = args['start_from'], min_digits = args['min_digits'],
                sequential = args['sequential'], by_directory = args['by_directory'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    def add_date(self, args):
        Renamer.add_date(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                as_prefix = args['as_prefix'], join_str = args['join_str'],
                format = args['format'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    def add_text(self, args):
        Renamer.add_text(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                text = args['text'],
                as_prefix = args['as_prefix'], join_str = args['join_str'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    def remove(self, args):
        Renamer.remove_n_characters(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                num_chars = args['num_chars'], from_head = not args['from_tail'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    def replace(self, args):
        Renamer.replace(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                find_str = args['find_str'],
                replace_str = args['replace_str'] if 'replace_str' in args else None,
                case_insensitive = args['ignore_case'],
                include_extension = args['include_extension'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    def capitalize(self, args):
        Renamer.capitalize(src_dir = args['dir'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

    def delete(self, args):
        Renamer.delete(src_dir = args['dir'],
                non_media_files_only = args['non_media_files_only'],
                sort = args['sort'], nested_indent = args['nested_indent'],
                end_level = args['end_level'],
                include = args['include'], exclude = args['exclude'],
                filter_dirs = args['filter_dirs'], filter_files = not args['all_files'],
                include_dirs = args['include_dirs'], include_files = not args['exclude_files'],
                display_current = args['display_current'], quiet = args['quiet'])

def main():
    ''' Renamer entry point
    '''
    RenameDispatcher().dispatch()
